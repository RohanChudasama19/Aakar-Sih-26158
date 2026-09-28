# Metric Definitions

## 1. Point Density
- **Definition**: Number of dense cloud vertices within a $ radius sphere of the query location.
- **Normalization**: Computed as volumetric density or projected surface density depending on local curvature.
- **Handling**: Boundary edges default to low density.

## 2. Surface Support
- **Definition**: Minimum Euclidean distance from a mesh face centroid to the nearest un-filtered dense cloud point.
- **Weak-support**: Faces with distances $> \epsilon$ are weak.

## 3. Camera Observations
- **Definition**: Number of verified camera frustums intersecting the query point.
- **Label**: POTENTIAL_CAMERA_VISIBILITY (since full occlusion raycasting across 7.5M points is computationally prohibitive in real-time).

## 4. Reconstruction Risk
- **Definition**: Boolean or scalar fusion of low surface support and low point density. 
- **Interpretation**: Not a substitute for geometric accuracy. It highlights interpolation vs observation.

## 5. Independent Geometric Error
- **Status**: GEOMETRIC_ERROR_AVAILABLE = FALSE for MARS. 
- **Condition**: Awaiting verified absolute ground control points (GCPs).
