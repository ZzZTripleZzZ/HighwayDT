"""Cycle CARLA weather presets and set a matching road friction.

The script connects to a running CARLA server and does not change the map or the
world settings, so it can run next to another client such as the SUMO co-simulation.
Every ``--interval`` seconds of wall-clock time it picks a random weather preset and
replaces the friction box with one that has the friction value of that preset.

Friction area: there is no ego vehicle in this script, so one box centered on the map
origin covers the whole map. Its default half size of 10 km is the size that CARLA's
scenario_runner uses for the same purpose.

Destroying a friction box does not give the vehicles inside their earlier friction
back. On exit the script therefore replaces the last box with one at CARLA's default
tire friction of 3.5, waits for the server to apply it, and then destroys it. It also
restores the weather it found.
"""

import argparse
import random
import time

import carla

from friction_trigger import DEFAULT_TIRE_FRICTION, destroy_actors, replace_friction_trigger

# Friction value of each weather preset, keyed by the preset name in carla.WeatherParameters
FRICTION_BY_PRESET = {
    'ClearNoon': 1.0,
    'CloudyNoon': 0.9,
    'WetNoon': 0.8,
    'MidRainyNoon': 0.7,
    'HardRainNoon': 0.6,
    'SoftRainNoon': 0.7,
    'ClearSunset': 1.0,
    'CloudySunset': 0.9,
    'WetSunset': 0.8,
    'MidRainSunset': 0.7,
    'HardRainSunset': 0.6,
    'SoftRainSunset': 0.7,
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--host', default='127.0.0.1', help='CARLA server host (default: 127.0.0.1)')
    parser.add_argument('-p', '--port', type=int, default=2000, help='CARLA server port (default: 2000)')
    parser.add_argument('--cycles', type=int, default=20,
                        help='number of weather changes before the script exits (default: 20)')
    parser.add_argument('--interval', type=float, default=3.0,
                        help='seconds between two weather changes (default: 3.0)')
    parser.add_argument('--friction-half-size', type=float, default=10000.0,
                        help='half size of the friction box in meters (default: 10000)')
    parser.add_argument('--seed', type=int, default=None, help='random seed for the preset choice')
    return parser.parse_args()


def main():
    args = parse_args()
    random.seed(args.seed)

    client = carla.Client(args.host, args.port)
    client.set_timeout(10.0)
    world = client.get_world()
    original_weather = world.get_weather()

    center = carla.Location(0.0, 0.0, 0.0)
    trigger = None
    try:
        for cycle in range(args.cycles):
            name = random.choice(list(FRICTION_BY_PRESET))
            friction = FRICTION_BY_PRESET[name]
            world.set_weather(getattr(carla.WeatherParameters, name))
            trigger = replace_friction_trigger(world, trigger, friction, center, args.friction_half_size)
            print(f'[{cycle + 1}/{args.cycles}] weather {name}, friction {friction}')
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print('Interrupted by user.')
    finally:
        if trigger is not None:
            # The default box must exist for at least one simulation step before it is destroyed
            trigger = replace_friction_trigger(world, trigger, DEFAULT_TIRE_FRICTION, center,
                                               args.friction_half_size)
            try:
                for _ in range(2):
                    world.wait_for_tick(5.0)
            except RuntimeError:
                print('No simulation step within 5 s, so the vehicles may keep the last friction value.')
        destroy_actors([trigger])
        world.set_weather(original_weather)
        print(f'Friction reset to {DEFAULT_TIRE_FRICTION}, friction box destroyed and original weather restored.')


if __name__ == '__main__':
    main()
