"""Record a truck on autopilot under changing weather and road friction.

The script loads ``--map`` (default Town07), spawns a CarlaCola truck with a chase
camera, and records the camera to ``--out``. It runs the world in synchronous mode
with a fixed step of 1/30 s, so the 30 fps video plays in simulation time. Every
``--interval`` simulated seconds it picks a random weather preset and replaces the
friction box with one that has the friction value of that preset.

Friction area: the box is centered on the truck each time the preset changes, with a
default half size of 100 m. Choose ``--friction-half-size`` larger than the distance
the truck drives in one interval, otherwise the truck leaves the box and CARLA gives
its wheels their previous friction back.

On exit the script destroys the friction box, the camera and the truck, and restores
the world settings and the Traffic Manager mode.
"""

import argparse
import os
import random

import carla
import cv2
import numpy as np

from friction_trigger import destroy_actors, replace_friction_trigger

FPS = 30
IMAGE_WIDTH, IMAGE_HEIGHT = 800, 600

# Friction value of each weather preset, keyed by the preset name in carla.WeatherParameters
FRICTION_BY_PRESET = {
    'ClearNoon': 1.0,
    'HardRainNoon': 0.5,
    'ClearSunset': 1.0,
    'HardRainSunset': 0.5,
    'WetNoon': 0.7,
    'WetSunset': 0.7,
    'MidRainSunset': 0.5,
}

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Video', 'output.mp4')


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--host', default='127.0.0.1', help='CARLA server host (default: 127.0.0.1)')
    parser.add_argument('-p', '--port', type=int, default=2000, help='CARLA server port (default: 2000)')
    parser.add_argument('--tm-port', type=int, default=8000, help='Traffic Manager port (default: 8000)')
    parser.add_argument('--map', default='Town07', help='CARLA map to load (default: Town07)')
    parser.add_argument('--duration', type=float, default=60.0,
                        help='simulated seconds to record (default: 60)')
    parser.add_argument('--interval', type=float, default=3.0,
                        help='simulated seconds between two weather changes (default: 3.0)')
    parser.add_argument('--friction-half-size', type=float, default=100.0,
                        help='half size of the friction box around the truck in meters (default: 100)')
    parser.add_argument('--out', default=DEFAULT_OUT,
                        help='output video file (default: Video/output.mp4 at the repository root)')
    parser.add_argument('--seed', type=int, default=None, help='random seed for spawn point and presets')
    return parser.parse_args()


def spawn_hgv(world, blueprint_library):
    spawn_points = world.get_map().get_spawn_points()

    # Use the first spawn point with x < -100 m and y < -100 m. If the map has none,
    # use a random spawn point.
    chosen_spawn_point = None
    for sp in spawn_points:
        if sp.location.y < -100 and sp.location.x < -100:
            chosen_spawn_point = sp
            break
    if chosen_spawn_point is None:
        chosen_spawn_point = random.choice(spawn_points)

    hgv_bp = blueprint_library.filter('vehicle.carlamotors.carlacola')[0]
    return world.spawn_actor(hgv_bp, chosen_spawn_point)


def attach_camera_to_vehicle(world, vehicle):
    camera_bp = world.get_blueprint_library().find('sensor.camera.rgb')
    camera_bp.set_attribute('image_size_x', str(IMAGE_WIDTH))
    camera_bp.set_attribute('image_size_y', str(IMAGE_HEIGHT))

    # Chase view: 15 m behind and 15 m above the truck, pitched 30 degrees down
    camera_transform = carla.Transform(carla.Location(x=-15, z=15), carla.Rotation(pitch=-30))
    return world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)


def process_camera_image(image, video_writer):
    # CARLA delivers BGRA bytes. Drop the alpha channel and write the BGR frame.
    array = np.frombuffer(image.raw_data, dtype=np.dtype('uint8'))
    array = np.reshape(array, (image.height, image.width, 4))
    video_writer.write(np.ascontiguousarray(array[:, :, :3]))


def main():
    args = parse_args()
    random.seed(args.seed)

    client = carla.Client(args.host, args.port)
    client.set_timeout(30.0)
    world = client.load_world(args.map)
    blueprint_library = world.get_blueprint_library()

    traffic_manager = client.get_trafficmanager(args.tm_port)
    original_settings = world.get_settings()
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = 1.0 / FPS
    world.apply_settings(settings)
    traffic_manager.set_synchronous_mode(True)

    hgv = camera = trigger = video_writer = None
    try:
        out_dir = os.path.dirname(os.path.abspath(args.out))
        os.makedirs(out_dir, exist_ok=True)
        video_writer = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*'mp4v'), FPS,
                                       (IMAGE_WIDTH, IMAGE_HEIGHT))

        hgv = spawn_hgv(world, blueprint_library)
        camera = attach_camera_to_vehicle(world, hgv)
        camera.listen(lambda image: process_camera_image(image, video_writer))
        hgv.set_autopilot(True, args.tm_port)
        world.tick()   # the truck has a valid location only after the first tick

        total_steps = int(round(args.duration * FPS))
        steps_per_change = max(1, int(round(args.interval * FPS)))
        for step in range(total_steps):
            if step % steps_per_change == 0:
                name = random.choice(list(FRICTION_BY_PRESET))
                friction = FRICTION_BY_PRESET[name]
                world.set_weather(getattr(carla.WeatherParameters, name))
                trigger = replace_friction_trigger(world, trigger, friction, hgv.get_location(),
                                                   args.friction_half_size)
                print(f't = {step / FPS:6.1f} s: weather {name}, friction {friction}')
            world.tick()
    except KeyboardInterrupt:
        print('Interrupted by user.')
    finally:
        if camera is not None:
            camera.stop()
        destroy_actors([trigger, camera, hgv])
        traffic_manager.set_synchronous_mode(False)
        world.apply_settings(original_settings)
        if video_writer is not None:
            video_writer.release()
            print(f'Video saved as {args.out}')


if __name__ == '__main__':
    main()
