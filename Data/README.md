# Data

`Snowy_I-695_Sample01.csv` is a sample of the vehicle trajectories behind HighwayDT. A drone recorded the Interstate 695 segment in Baltimore, Maryland, on January 15, 2024, in snowy conditions, and the 4K video at 30 frames per second was processed into trajectories.

The sample covers 113 vehicles over about 300 s, with one row per vehicle every 1/30 s.

| Column | Meaning |
|:---|:---|
| `Vehicle ID` | Track identifier |
| `Type` | `Car`, `Medium Vehicle` or `Heavy Vehicle`, each with a leading space in the file |
| `x [m]`, `y [m]` | Planar position in meters |
| `Speed [km/h]` | Speed |
| `Tan. Acc. [ms-2]`, `Lat. Acc. [ms-2]` | Tangential and lateral acceleration in m/s² |
| `Time [s]` | Time since the start of the recording |
| ` Angle [rad]` | Heading. The column name starts with a space |

Each track ends with one row that has only `Vehicle ID` and `Type` filled. `Sample.ipynb` removes these rows with `dropna()`.

`Sample.ipynb` calibrates the Intelligent Driver Model on one vehicle of this sample with a genetic algorithm. `Guidelines for Calibrating Car-Following Models.pdf` explains the calibration procedure. Run the notebook from this folder, since it reads the CSV by relative path. The CSV has no lane or vehicle length column. The notebook infers lanes from the lateral offset to the road axis and assigns a nominal length by `Type`. Both are assumptions stated in the notebook.
