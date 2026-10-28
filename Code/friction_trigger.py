"""Road friction in CARLA through a friction trigger volume.

CARLA has no global road friction setting. The blueprint ``static.trigger.friction``
spawns a box volume with a ``friction`` value. When a vehicle enters the box, CARLA
saves the friction of its wheels and applies the box's value to all four wheels. When
the vehicle leaves the box, CARLA restores the saved values. This is the approach of
the ``ChangeRoadFriction`` behavior in CARLA's scenario_runner.

The ``extent_x``, ``extent_y`` and ``extent_z`` attributes are half sizes of the box in
Unreal units, which are centimeters. CARLA passes them to the box component without
converting meters (see ``Trigger/TriggerFactory.cpp`` in the CARLA repository). The
functions below take meters and convert them.
"""

import carla

FRICTION_BLUEPRINT = 'static.trigger.friction'


def spawn_friction_trigger(world, friction, center, half_size_m, half_height_m=50.0):
    """Spawn one friction box centered on ``center`` (a carla.Location in meters).

    The box covers ``2 * half_size_m`` by ``2 * half_size_m`` meters horizontally and
    ``2 * half_height_m`` meters vertically. Returns the trigger actor.
    """
    blueprint = world.get_blueprint_library().find(FRICTION_BLUEPRINT)
    blueprint.set_attribute('friction', str(friction))
    blueprint.set_attribute('extent_x', str(half_size_m * 100.0))
    blueprint.set_attribute('extent_y', str(half_size_m * 100.0))
    blueprint.set_attribute('extent_z', str(half_height_m * 100.0))
    transform = carla.Transform(carla.Location(x=center.x, y=center.y, z=center.z), carla.Rotation())
    return world.spawn_actor(blueprint, transform)


def replace_friction_trigger(world, old_trigger, friction, center, half_size_m, half_height_m=50.0):
    """Destroy ``old_trigger`` (if any) and spawn a new box with ``friction``.

    Only one box exists at a time. Each box saves the wheel values a vehicle had when
    it entered, so with overlapping boxes a vehicle could get the value of another box
    back when it leaves one of them.
    """
    if old_trigger is not None:
        old_trigger.destroy()
    return spawn_friction_trigger(world, friction, center, half_size_m, half_height_m)


def destroy_actors(actors):
    """Destroy every actor in ``actors`` that is not None and still alive."""
    for actor in actors:
        if actor is not None and actor.is_alive:
            actor.destroy()
