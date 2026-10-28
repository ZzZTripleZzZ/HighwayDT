# Known issues

These issues were found by a static review of the release on 2026-10-28. No script or notebook was executed, and CARLA and SUMO were not run. CARLA API facts were checked against the CARLA documentation at https://carla.readthedocs.io (Python API reference, blueprint library, sensor reference).

## Fixed in this release

| File | Location | Fix |
|:---|:---|:---|
| `Code/LidarData_compar.py` | imports | Removed the unused `glob` and `sys` imports (pyflakes). |
| `Code/LidarData_compar.py` | main loop | Removed the unused `world_frame = world.get_snapshot().frame` assignment (pyflakes). |
| `Code/Town_07_truck_weather_change.py` | `attach_camera_to_vehicle` | `image_size_x` and `image_size_y` were set on the blueprint after the camera was spawned, so they had no effect. They are now set before `spawn_actor`. The values equal the CARLA defaults (800 x 600), so the output does not change. |
| `Code/Town_07_truck_weather_change.py` | `main` | The video went to `../Video/output.mp4` relative to the working directory, and that folder did not exist, so `cv2.VideoWriter` could not open the file and nothing was saved. The path is now `Video/output.mp4` at the repository root, and the folder is created first. |

## Open issues

### `Code/Weather_friction_change.py` and `Code/Town_07_truck_weather_change.py`

- **Road friction never changes.** `set_road_friction` (lines 47 to 53 and 38 to 44) only acts on actors whose `type_id` contains `static.trigger`. A freshly loaded world has no such actor, so the loop body never runs. The CARLA blueprint library lists the friction trigger as `static.trigger.friction`, with attributes `friction`, `extent_x`, `extent_y`, `extent_z` and `role_name`. The call `find('static.trigger')` therefore names a blueprint that does not exist. If a trigger did exist, the function would also spawn a new trigger at its position every 3 s without setting the extent and without destroying the old one. A working version needs a decision on where the trigger volumes go and how large they are, which this release does not invent.
- **Weather presets as dict keys.** `friction_values` uses `carla.WeatherParameters` presets as dictionary keys. The CARLA documentation lists `__eq__` and `__ne__` for `WeatherParameters` but no `__hash__`, so it is not confirmed that these objects are hashable. All preset names used do exist in the documented list.
- **Endless loop and no cleanup.** `change_weather_and_friction` loops forever. In `Town_07_truck_weather_change.py` the `time.sleep(60)` at line 107 is unreachable, and the truck and the camera are never destroyed on exit. Only `camera.stop()` and `video_writer.release()` run.
- **Comments that disagree with the code.** The comments are in Chinese and several do not match the code: line 44 of `Weather_friction_change.py` says the weather changes every 10 s but the code sleeps 3 s. In `Town_07_truck_weather_change.py`, line 52 says `y < -50` but the code uses `y < -100` and `x < -100`, line 56 says the first spawn point is the fallback but the code uses `random.choice`, and line 68 says the camera sits 6 m behind and 2.5 m above the truck but the code uses `x=-15, z=15`.
- **Map.** `Town_07_truck_weather_change.py` loads `Town07`, a rural map. The co-simulation demo in the README uses `Town04`.

### `Code/LidarData_compar.py`

- The name suggests a comparison, but the script only records a top-down view of one LiDAR point cloud per frame into `_out/lidar_output.mp4`. No comparison against other data happens.
- `cm.get_cmap('viridis')` at line 9 is deprecated since Matplotlib 3.7, and Matplotlib 3.10 warns that it will be removed in 3.11. `matplotlib.colormaps['viridis']` is the replacement.
- `intensity /= max_intensity` at line 99 divides by zero when every point has zero intensity.
- The script turns on Traffic Manager synchronous mode at line 22 but does not turn it off in the `finally` block. Only the world settings are restored.

### `Data/Sample.ipynb`

Every name is defined before use when the cells run in order. `df1` is created in cell 3 by the `groupby(...).apply(...)` call, and `dt`, `num_steps`, `IDM_param_bounds` and `idmbest_params` are all created in cell 8 before cells 9 to 11 use them. A pyflakes pass over the concatenated cells reports no undefined names. The problems are in the method and the labels.

- **Cell 4, uneven time step.** `df1.iloc[2::6]` keeps every sixth row of the table that holds all vehicles at each time stamp, not every sixth frame of one vehicle. With 2 to 8 vehicles per frame, the rows kept for vehicle 104 are spaced between 0.10 s and 1.60 s apart. Cells 8 and 10 integrate the IDM with a fixed `dt = 0.2`, so the simulated and recorded trajectories are not on the same time axis. Subsampling each vehicle's own rows, for example `df1.groupby('Vehicle ID', group_keys=False).apply(lambda g: g.iloc[::6])`, would give a 0.2 s step, but the stored outputs and the reported RMSE would then change.
- **Cell 3, leader search ignores lanes.** `find_leading_vehicle_and_gap_speed_vectorized` picks the nearest vehicle ahead by longitudinal position among all vehicles in the frame, in any lane. The leader of vehicle 104 can therefore be a vehicle in an adjacent lane.
- **Cell 2, position and length.** The longitudinal position is the Euclidean distance from the minimum `x` and `y` corner, which follows the road only on a straight segment. Every vehicle, trucks included, is given a length of 5 m.
- **Cell 8, bounds differ from the README and the guideline.** `IDM_param_bounds` sets `v0` to `(8, 33)`. The text states an upper bound of 33.6 m/s and asks for a lower bound above the highest observed speed. The highest speed in the sample is about 15.7 m/s, and about 11.4 m/s for vehicle 104, so the lower bound of 8 m/s is below both.
- **Cell 8 versus cell 10, different simulators.** The calibration run `idmrun_simulation` lets the speed go negative, while the evaluation run `run_model_simulation` clips it at zero. The calibrated parameters are therefore scored with a slightly different model than the one they were fitted on.
- **Cell 8, comment.** The comment on `vFollInitial` says the following vehicle starts from rest, but the code uses its recorded initial speed.
- **Cell 6, pandas warning.** `veh` is a slice of `df1`, so the `.loc` assignments raise `SettingWithCopyWarning` (visible in the stored output). `veh = df1[...].copy()` in cell 5 avoids it.
- **Cell 10, comment.** "Calculate acceleration and gap for IDM and CIDM" mentions CIDM, which the notebook does not contain.
- **Cell 11, unit label.** The acceleration axis reads `Acceleration (m$^2$)`. It should be m/s².
- These were not changed in the notebook because the stored outputs would then no longer match the code, and the notebook was not re-run.

### Documentation (`docs/source`)

- `instructions.rst`, section "Setting Up Co-Simulation", clones `https://github.com/example/sumo-carla-co-simulation.git`, which is a placeholder, and then runs `run_co_simulation.py` and installs `requirements.txt`. None of these exist in this repository. `guide.rst` refers to the same `run_co_simulation.py` and a `scenarios/` folder. CARLA's own co-simulation entry point is `Co-Simulation/Sumo/run_synchronization.py` inside the CARLA package (https://carla.readthedocs.io/en/latest/adv_sumo/).
- `conf.py` sets `html_static_path = ['_static']`, but `docs/source/_static` does not exist. Sphinx warns about it but still builds.
- The Read the Docs project and `conf.py` still use the name `nsf_oac`.

### Not in this repository

- The SUMO network and configuration of the Interstate 695 segment, the calibrated IDM inside SUMO, and the HighwayDT co-simulation scenarios used in the paper.
- The federated reinforcement learning training, attack and defense code of the paper.
