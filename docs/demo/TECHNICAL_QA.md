# TECHNICAL Q&A PREPARATION

Q: Is this actually running offline?
A: Yes. If we disable the network adapter, all assets, models, and Vite bundles load from 127.0.0.1:8000. There are zero CDN dependencies.

Q: How did you calculate Point Density?
A: We use a spherical-volume proximity search around mesh face centroids against the dense point cloud, avoiding misleading 'surface density' assumptions.

Q: Why is Geometric Error unavailable?
A: Because true geometric error requires independent ground-truth reference data (like RTK GPS or LiDAR). Fabricating it based on internal reprojection error is scientifically dishonest.

Q: Are you using Gaussian Splatting?
A: No. We use explicit mesh geometry (GLB/PLY) because it allows deterministic topological indexing, precise distance measurements, and verifiable quality metrics that splatting currently obscures.
