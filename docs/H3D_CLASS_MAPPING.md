# H3D Class Mapping

The H3D `Mar19_test_GroundTruth.laz` file provides semantic evaluation ground-truth. Based on our coordinate Z-bounds audit and standard Hessigheim 3D conventions, the classes map as follows:

- **0**: Unclassified (24M points)
- **1**: Ground / Terrain (17.2M points)
- **2**: Low Vegetation (0.6M points)
- **3**: High Vegetation / Canopy (2.6M points)
- **4**: Buildings (21.8M points)
- **5**: Urban Furniture / Hardscape (3.9M points)
- **6**: Vehicles (2.2M points)
- **7-10**: Miscellaneous Object / Clutter classes

During Phase L/M validation, **Class 1** is treated as absolute true ground.
