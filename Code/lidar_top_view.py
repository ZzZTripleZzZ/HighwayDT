"""Record a top view of the LiDAR point cloud of a car on autopilot in CARLA.

The script spawns a Lincoln MKZ 2017 with a ray-cast LiDAR at the first spawn point
of the current map, runs the world in synchronous mode with a 0.05 s step, and draws
each LiDAR sweep from above, colored by intensity. The frames are written to ``--out``.
On exit it destroys the car and the sensor and restores the world settings and the
Traffic Manager mode.
"""

import argparse
import os
from queue import Queue, Empty

import carla
import cv2
import matplotlib
import numpy as np

VIRIDIS = np.array(matplotlib.colormaps['viridis'].colors)
VID_RANGE = np.linspace(0.0, 1.0, VIRIDIS.shape[0])
FIXED_DELTA_SECONDS = 0.05
PIXELS_PER_METER = 5

def sensor_callback(data, queue):
    queue.put(data)

def record(args):
    client = carla.Client(args.host, args.port)
    client.set_timeout(10.0)
    world = client.get_world()
    bp_lib = world.get_blueprint_library()

    traffic_manager = client.get_trafficmanager(args.tm_port)
    original_settings = world.get_settings()
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = FIXED_DELTA_SECONDS
    world.apply_settings(settings)
    traffic_manager.set_synchronous_mode(True)

    vehicle = None
    lidar = None
    video_writer = None
    previous_frame_data = None

    try:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)

        vehicle_bp = bp_lib.filter("vehicle.lincoln.mkz_2017")[0]
        lidar_bp = bp_lib.filter("sensor.lidar.ray_cast")[0]

        lidar_bp.set_attribute('range', str(args.range))
        lidar_bp.set_attribute('points_per_second', str(args.points_per_second))
        lidar_bp.set_attribute('channels', str(args.channels))
        lidar_bp.set_attribute('upper_fov', str(args.upper_fov))
        lidar_bp.set_attribute('lower_fov', str(args.lower_fov))
        if args.no_noise:
            lidar_bp.set_attribute('dropoff_general_rate', '0.0')
            lidar_bp.set_attribute('dropoff_intensity_limit', '1.0')
            lidar_bp.set_attribute('dropoff_zero_intensity', '0.0')

        spawn_points = world.get_map().get_spawn_points()
        selected_spawn_point = spawn_points[0]

        vehicle = world.spawn_actor(
            blueprint=vehicle_bp,
            transform=selected_spawn_point)
        vehicle.set_autopilot(True, args.tm_port)
        traffic_manager.vehicle_percentage_speed_difference(vehicle, 50)  # drive 50% below the speed limit

        lidar_transform = carla.Transform(
            carla.Location(x=0.0, z=2.5),
            carla.Rotation(pitch=-10))

        lidar = world.spawn_actor(
            blueprint=lidar_bp,
            transform=lidar_transform,
            attach_to=vehicle)

        # One video frame per simulation step, so the video plays in simulation time
        fps = round(1.0 / FIXED_DELTA_SECONDS)
        video_writer = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*'mp4v'), fps, (args.width, args.height))

        lidar_visualization = np.zeros((args.height, args.width, 3), dtype=np.uint8)
        lidar_queue = Queue()
        lidar.listen(lambda data: sensor_callback(data, lidar_queue))

        for frame in range(args.frames):
            world.tick()

            try:
                lidar_data = lidar_queue.get(True, 1.0)
            except Empty:
                print("[Warning] Some sensor data has been missed")
                continue

            p_cloud_size = len(lidar_data)
            p_cloud = np.frombuffer(lidar_data.raw_data, dtype=np.dtype('f4'))
            p_cloud = np.reshape(p_cloud, (p_cloud_size, 4))

            if p_cloud_size == 0:
                print(f"Frame {frame+1}/{args.frames}: No LiDAR points captured.")
                continue

            lidar_visualization[:] = 0

            # Normalize intensity to [0, 1] within the sweep. A sweep with zero or
            # negative maximum intensity is drawn with the lowest color.
            intensity = np.array(p_cloud[:, 3])
            max_intensity = np.max(intensity)
            if max_intensity > 0:
                intensity = np.clip(intensity / max_intensity, 0.0, 1.0)
            else:
                intensity = np.zeros_like(intensity)

            # Top view: sensor x (forward) to image columns, sensor y (right) to image rows
            u_coord = (p_cloud[:, 0] * PIXELS_PER_METER + args.width // 2).astype(np.int32)
            v_coord = (p_cloud[:, 1] * PIXELS_PER_METER + args.height // 2).astype(np.int32)

            valid_mask = (u_coord >= 0) & (u_coord < args.width) & (v_coord >= 0) & (v_coord < args.height)
            u_coord = u_coord[valid_mask]
            v_coord = v_coord[valid_mask]
            intensity = intensity[valid_mask]

            # OpenCV images are BGR, so the viridis channels go in reverse order
            color_map = np.array([
                np.interp(intensity, VID_RANGE, VIRIDIS[:, 2]) * 255.0,
                np.interp(intensity, VID_RANGE, VIRIDIS[:, 1]) * 255.0,
                np.interp(intensity, VID_RANGE, VIRIDIS[:, 0]) * 255.0]).astype(np.int32).T

            for i in range(len(u_coord)):
                cv2.circle(lidar_visualization, (u_coord[i], v_coord[i]), args.dot_extent, color_map[i].tolist(), -1)

            # Blend current frame with previous frame data to reduce flickering
            if previous_frame_data is not None:
                lidar_visualization = cv2.addWeighted(lidar_visualization, 0.5, previous_frame_data, 0.5, 0)

            previous_frame_data = lidar_visualization.copy()

            video_writer.write(lidar_visualization)

            print(f"Frame {frame+1}/{args.frames} processed.")

    finally:
        # Restore the world settings before destroying the car. Destroying a car that the
        # Traffic Manager still drives in synchronous mode aborts the client with
        # "trying to operate on a destroyed actor".
        if lidar is not None:
            lidar.stop()
        if vehicle is not None:
            vehicle.set_autopilot(False, args.tm_port)
        traffic_manager.set_synchronous_mode(False)
        world.apply_settings(original_settings)
        for actor in (lidar, vehicle):
            if actor is not None and actor.is_alive:
                actor.destroy()
        if video_writer is not None:
            video_writer.release()
            print(f"LiDAR video saved as {args.out}")

def main():
    argparser = argparse.ArgumentParser(
        description='Record a top view of a CARLA LiDAR point cloud to a video')
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='CARLA server port (default: 2000)')
    argparser.add_argument(
        '--tm-port',
        metavar='P',
        default=8000,
        type=int,
        help='Traffic Manager port (default: 8000)')
    argparser.add_argument(
        '--res',
        metavar='WIDTHxHEIGHT',
        default='800x600',
        help='video resolution (default: 800x600)')
    argparser.add_argument(
        '-f', '--frames',
        metavar='N',
        default=500,
        type=int,
        help='number of frames to record (default: 500)')
    argparser.add_argument(
        '-o', '--out',
        metavar='FILE',
        default=os.path.join('_out', 'lidar_output.mp4'),
        help='output video file (default: _out/lidar_output.mp4)')
    argparser.add_argument(
        '-d', '--dot-extent',
        metavar='SIZE',
        default=1,
        type=int,
        help='radius of each drawn point in pixels, 1 to 4 works well (default: 1)')
    argparser.add_argument(
        '--no-noise',
        action='store_true',
        help='remove the drop off and noise from the normal (non-semantic) lidar')
    argparser.add_argument(
        '--upper-fov',
        metavar='F',
        default=30.0,
        type=float,
        help='lidar\'s upper field of view in degrees (default: 30.0)')
    argparser.add_argument(
        '--lower-fov',
        metavar='F',
        default=-30.0,
        type=float,
        help='lidar\'s lower field of view in degrees (default: -30.0)')
    argparser.add_argument(
        '-c', '--channels',
        metavar='C',
        default=64,
        type=int,
        help='lidar\'s channel count (default: 64)')
    argparser.add_argument(
        '-r', '--range',
        metavar='R',
        default=100.0,
        type=float,
        help='lidar\'s maximum range in meters (default: 100.0)')
    argparser.add_argument(
        '--points-per-second',
        metavar='N',
        default=100000,
        type=int,
        help='lidar points per second (default: 100000)')
    args = argparser.parse_args()
    args.width, args.height = [int(x) for x in args.res.split('x')]

    try:
        record(args)

    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')

if __name__ == '__main__':
    main()

