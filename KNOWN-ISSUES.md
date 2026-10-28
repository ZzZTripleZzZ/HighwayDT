# Known issues

The defects found by the static review of 2026-10-28 are fixed, see the git history. This file lists what remains. The items below need a running CARLA server to check, or they are limits of the data and the method.

## CARLA scripts (`Code/`)

The scripts compile and pass pyflakes, and their control flow was tested against a stand-in for the `carla` module. They have not been run against a CARLA server since the revision. CARLA API calls were checked against the Python API reference and the blueprint library at https://carla.readthedocs.io.

- **Friction trigger behavior.** `friction_trigger.py` follows the `ChangeRoadFriction` behavior of CARLA's scenario_runner: destroy the old `static.trigger.friction` box, then spawn a new one. Three points come from CARLA's source code, not from its documentation, and a CARLA run should confirm them. The `extent_x/y/z` attributes are half sizes in centimeters (`Trigger/TriggerFactory.cpp`). A vehicle already inside a box when the box is spawned receives its friction. Destroying a box gives the vehicles inside their previous friction back (`Trigger/FrictionTrigger.cpp` restores it when a vehicle leaves the box).
- **Friction values.** The values per weather preset (0.5 to 1.0) are the original authors' choice. CARLA applies them as the friction of every wheel. The default `tire_friction` of `carla.WheelPhysicsControl` is 2.0 in the documentation, and the friction trigger's own default is 3.5, so a value of 1.0 may be more slippery than the vehicle's default rather than equal to a dry road. Reading `vehicle.get_physics_control().wheels` in a running CARLA would settle this.
- **Several vehicles in one box.** CARLA's friction trigger stores one set of saved wheel values per box. With many vehicles inside the map-wide box of `Weather_friction_change.py`, for example during the co-simulation, a vehicle may get another vehicle's saved values back when the box is replaced. This is CARLA's behavior, not the script's.
- **Truck leaving its box.** `Town_07_truck_weather_change.py` centers the box on the truck at each weather change. If the truck drives farther than `--friction-half-size` within one `--interval`, it leaves the box and gets its previous friction back until the next change.

## `Data/Sample.ipynb`

- **One vehicle.** The calibration uses one car-following pair, vehicle 104 behind vehicle 97, for 12.4 s. Across GA seeds 0 (the notebook's) to 3, the gap RMSE stays between 0.17 and 0.18 m, but $s_0$ ranges from 2.6 to 3.7 m, $T$ from 0.29 to 0.42 s and $v_0$ from 19 to 29 m/s. One short trajectory does not fix all five parameters.
- **Assumed quantities.** The CSV has no lane, length or reference point column. The notebook assumes a 3.66 m lane width, nominal lengths of 5 m (`Car`), 8 m (`Medium Vehicle`) and 16 m (`Heavy Vehicle`), and that `x [m]`, `y [m]` mark the vehicle center. In the sample, 98% of the positions lie within 1 m of the road axis, and the lane test does not change the leader of vehicle 104.

## Documentation

- The Read the Docs project and `docs/source/conf.py` still use the name `nsf_oac`.

## Not in this repository

- The SUMO network and configuration of the Interstate 695 segment, the calibrated IDM inside SUMO, and the HighwayDT co-simulation scenarios used in the paper.
- The federated reinforcement learning training, attack and defense code of the paper.
