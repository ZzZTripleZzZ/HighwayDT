"""Road friction in CARLA through a friction trigger volume.

CARLA has no global road friction setting. The blueprint ``static.trigger.friction``
spawns a box volume with a ``friction`` value. When a vehicle enters the box, or is
inside it when the box is spawned, CARLA saves the friction of its wheels and applies
the box's value to all of its wheels. When the vehicle leaves the box, CARLA restores
the saved values. Destroying the box restores nothing: the vehicles inside keep the
box's value. This is the approach of the ``ChangeRoadFriction`` behavior in CARLA's
scenario_runner.

The value replaces ``tire_friction`` of every wheel in the vehicle's physics control.
In CARLA 0.9.15 every vehicle blueprint starts with a ``tire_friction`` of 3.5
(``DEFAULT_TIRE_FRICTION``), so a box value of 1.0 is already well below the default.

The ``extent_x``, ``extent_y`` and ``extent_z`` attributes are half sizes of the box in
Unreal units, which are centimeters. The functions below take meters and convert them.
These points were measured with CARLA 0.9.15.
"""

import carla

FRICTION_BLUEPRINT = 'static.trigger.friction'
DEFAULT_TIRE_FRICTION = 3.5   # tire_friction of every vehicle blueprint in CARLA 0.9.15


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

    Only one box exists at a time. Vehicles inside the old box keep its value until
    the new box applies its own, which happens at the next simulation step. Each box
    saves the wheel values a vehicle had when it entered, so with overlapping boxes a
    vehicle could get the value of another box back when it leaves one of them.
    """
    if old_trigger is not None:
        old_trigger.destroy()
    return spawn_friction_trigger(world, friction, center, half_size_m, half_height_m)


def destroy_actors(actors):
    """Destroy every actor in ``actors`` that is not None and still alive."""
    for actor in actors:
        if actor is not None and actor.is_alive:
            actor.destroy()
