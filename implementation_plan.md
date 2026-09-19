# Implementation Plan: AeroRecon Dataset-Driven Completion Program

This document details the architectural specifications, empirical evaluation protocols, and validation pipelines to complete the remaining capabilities of AeroRecon using real external UAV datasets.

---

## 0. Mandatory Technical Constraints & Guiding Principles

### A. GCP Control Point Requirements
- **Minimum Threshold**: At least **4 non-collinear CONTROL points** are required for georeferencing alignment; **6 to 10 points** are recommended for production surveys.
- **Geometric Distribution Validation**: The system must evaluate and flag weak control geometries:
  - Tightly clustered points (insufficient spatial spread)
  - Degenerate collinear or near-collinear arrangements
  - Sub-optimal bounding area coverage across the reconstruction domain
  - Inadequate vertical/elevation diversity where 3D tilt and elevation accuracy matter
- **Estimation & Separation**:
  - Fitting must use weighted least-squares (WLS) accounting for known control point measurement uncertainties ($\sigma_x, \sigma_y, \sigma_z$) where available, coupled with robust outlier rejection (RANSAC / Huber loss).
  - **Strict Independence**: `CHECKPOINT` points are completely excluded from Sim(3) alignment estimation. They are evaluated strictly post-alignment as validation targets.

### B. Surface Validation Metrics
- **3D vs. Vertical Separation**: Generic Cloud-to-Cloud (C2C) and Cloud-to-Mesh (C2M) nearest-surface euclidean distances must **never** be labeled as `RMSE_Z`.
- **Surface Validation Outputs**:
  - Mean Absolute 3D Surface Distance
  - Median 3D Surface Distance
  - RMSE_3D (Root Mean Square 3D Surface Distance)
  - P95 (95th percentile 3D distance)
  - Coverage Fraction (fraction of reference within validation threshold)
- **Vertical Metrics**: `RMSE_Z` and `MAE_Z` are reserved exclusively for comparisons conducted in a common horizontal reference grid (such as bare-earth DTM raster cell comparisons).

### C. Sensor Timeline & Interpolation Rules
- **Canonical Timeline**: All sensor streams must be indexed internally in Unix epoch seconds as `float64` with sub-second precision.
- **GPS / RTK Trajectory**:
  - Geodetic coordinates ($lat, lon$) must be converted to an appropriate metric Cartesian/projected coordinate frame (e.g. local ENU or UTM) prior to spatial interpolation.
  - Linear or cubic-spline interpolation must **never** be naively evaluated on angular latitude/longitude values.
- **Barometer**: Bounded linear interpolation with time-gap threshold rejection.
- **Accelerometer & Gyroscope**: Bounded linear interpolation between adjacent samples when synchronization requires it.
- **Orientation Quaternions**:
  - Must be interpolated strictly via **SLERP** (Spherical Linear Interpolation).
  - Quaternions must be normalized prior to and following interpolation.
  - Shortest-path sign handling ($q_1 \cdot q_2 < 0 \implies q_2 \leftarrow -q_2$) must be enforced.
  - Independent cubic interpolation of individual quaternion components ($w, x, y, z$) is strictly forbidden.

### D. IMU & SfM Integration Honesty
- The bundle adjustment (BA) pipeline must not assume stock COLMAP automatically supports arbitrary 6-DoF IMU covariance priors.
- An explicit audit of the installed COLMAP binary and PyCOLMAP API must precede implementation.
- If direct pose priors are unsupported by the installed build:
  - IMU signals will assist initial two-view selection, relative pose initialization, gravity-direction leveling, orientation regularization outside the BA loop, and post-SfM sensor fusion/trajectory evaluation.
  - The pipeline must **not** claim IMU-constrained bundle adjustment unless it genuinely executes in the underlying solver.

### E. Barometer Altitude Principles
- Barometer readings must be treated primarily as a **relative height sensor** ($\Delta h$) via the standard barometric formula.
- Integration must include ground-reference pressure calibration, temperature compensation where temperature telemetry exists, bias estimation, and drift compensation.
- Absolute vertical alignment must be anchored to GNSS/RTK elevation. Raw barometric altitude must **never** be presented as survey-grade absolute orthometric/ellipsoidal elevation.

### F. RTK / PPK Architecture
- **Two Distinct Modes**:
  1. *Trajectory Ingestion*: Parsing and ingesting pre-computed RTK/PPK solution CSVs, extracting solution quality flags (`RTK_FIXED`, `RTK_FLOAT`, `DGPS`, `PPK_FIXED`, `PPK_FLOAT`, `GNSS_SINGLE`, `UNKNOWN`), satellite count, and standard deviations / covariance matrices ($\sigma_x, \sigma_y, \sigma_z$).
  2. *Raw RINEX Processing*: Ingestion of raw RINEX observation and navigation files.
- **External Solvers**: AeroRecon will not implement a bespoke GNSS carrier-phase ambiguity solver from scratch. Ingestion and execution will wrap established external engines (such as RTKLIB / PPPH) where accessible, strictly documenting the solver name, version, configuration, and solution states.

### G. Semantic Model Licensing & Taxonomy
- Semantic model evaluation must independently verify:
  - UAVid dataset usage terms
  - Architecture implementation license (e.g., MIT/Apache-2.0)
  - Pretrained foundation weights license
  - Checkpoint redistribution rights
- If weights cannot be redistributed, support local path injection and exclude weights from the release bundle.
- **Reporting Separation**: The system must report official UAVid class metrics (IoU, precision, recall) separately from mapped AeroRecon taxonomy metrics (Building, Road, Vegetation, Obstacle, Ground, Unknown). The two must never be conflated.

### H. Dynamic Object Masking Protocol
- Mask generation must distinguish between:
  - `SEMANTIC_DYNAMIC_CANDIDATE` (single-frame semantic classification, e.g., moving car, human)
  - `TEMPORALLY_CONFIRMED_DYNAMIC` (objects exhibiting non-zero optical flow or inconsistent multi-view epipolar geometry across consecutive frames).
- Static vehicles or structural elements must not be aggressively pruned from SfM feature matching based on single-frame semantic classification alone unless explicitly configured in aggressive flight profiles.

### I. DTM Ground Filtering Methodology
- Digital Terrain Model (DTM) extraction must combine geometric ground filtering (e.g., Cloth Simulation Filter / Progressive Morphological Filter) with semantic classification evidence.
- The pipeline must produce an explicit **DTM confidence map** and an **observed coverage mask**. Large occluded or unobserved expanses must not be excessively interpolated and presented as measured ground.

### J. MARS-LVIG Timestamp Authority
- Original ROS bag header timestamps are the sole authoritative timeline.
- Frame extraction to MP4 video must not discard original sensor timing. An accompanying `frame_timestamps.csv` must record:
  - `frame_index`
  - `source_timestamp` (original ROS / sensor time)
  - `canonical_time_s`
  - `video_timestamp_s`
  - `source_identifier`
- All downstream sensor synchronization must reference `source_timestamp`.

### K. Performance Benchmark Definitions
- Benchmark timings must be partitioned and logged as:
  - `UPLOAD_TIME`
  - `QUEUE_WAIT_TIME`
  - `PIPELINE_PROCESSING_TIME`
  - `END_TO_END_TIME`
- Official SIH speed comparisons must explicitly state which metric is reported (default: `PIPELINE_PROCESSING_TIME` from cold start).

### L. Large-Scale SfM Claim Safety
- COLMAP mapper options (`INCREMENTAL`, `GLOBAL`, `HIERARCHICAL`) will be audited against installed binary capabilities.
- If hierarchical or global mappers are not compiled or supported, the system will record `NOT_AVAILABLE` rather than labeling an incremental mapper as hierarchical.

### M. Dataset Acquisition Strategy
- Datasets will not be downloaded in their entirety upfront.
- For each dataset: inspect official repository, verify license, determine accessibility requirements, inspect structure, and acquire only the minimal real representative subset necessary to prove the adapter before committing to large downloads.

---

## 1. Phased Roadmap

### Phase A: Dataset Acquisition & Inventory
- Establish `data_external/` directory tree (ignored via `.gitignore`):
  - `data_external/usegeo/`
  - `data_external/mars_lvig/`
  - `data_external/ppph_uav/`
  - `data_external/zurich_mav/`
  - `data_external/uavid/`
  - `data_external/h3d/`
- Compile `docs/DATASET_INVENTORY.md` cataloging URL, license, sensor streams, CRS, datums, durations, and validation uses.
- Compile `docs/DATASET_LICENSES.md` recording ownership, academic citations, commercial/demo permissions, and redistribution terms.

### Phase B: Dataset Adapters & Canonical Conversion Framework
- Define canonical AeroRecon mission layout in `docs/CANONICAL_DATASET_FORMAT.md`:
  ```
  mission/
      video/flight.mp4
      frames/optional_original_frames/
      telemetry/frame_timestamps.csv, gps.csv, imu.csv, barometer.csv, gimbal.csv, flight_metadata.json
      calibration/camera_intrinsics.json, camera_imu_extrinsics.json
      gnss/rtk_ppk.csv, rinex/
      control/gcps.csv, checkpoints.csv
      reference/lidar.las_or_laz, dtm.tif, orthophoto.tif, trajectory.csv
      semantics/images/, masks/, classes.json
  ```
- Build reusable adapter framework in `scripts/datasets/`:
  - `dataset_manifest.py`: Provenance manifest generator (checksums, URLs, local paths, licenses).
  - `validate_canonical_mission.py`: Strict schema, timestamp monotonicity, and unit validator.
  - `convert_mars_lvig.py`: ROS bag / raw sequence converter.
  - `convert_zurich_mav.py`: Zurich Urban MAV text/log sequence converter.
  - `convert_usegeo.py`: UseGeo photogrammetry & LiDAR reference converter.
  - `convert_uavid.py`: UAVid semantic sequence & mask converter.
  - `convert_h3d.py`: H3D Hessigheim benchmark LiDAR/DTM converter.
  - `prepare_ppph_uav.py`: PPPH-UAV RINEX/GNSS observation preparer.

### Phase C: MARS-LVIG Real Extraction
- Audit ROS bag reading capabilities (`rosbags` / ROS2 / MCAP).
- Enumerate real bag topics (RGB, IMU, GNSS, RTK, LiDAR).
- Extract RGB sequence, create `flight.mp4` and authoritative `frame_timestamps.csv`.
- Extract telemetry (`gps.csv`, `imu.csv`, `rtk_ppk.csv`, `flight_metadata.json`).

### Phases D through Z (Scheduled for Subsequent Milestones)
- Phase D: Canonical Sensor Time Synchronization (`app/pipeline/time_sync.py`)
- Phase E, F, G, H: IMU, Barometer, RTK/PPK Fusion & RINEX Handling
- Phase I: GCP Alignment (Weighted Sim(3), 4+ GCPs, Checkpoint Isolation)
- Phase J, K: 3D Surface Reference Validation & $\le 1\text{ m}$ Accuracy
- Phase L, M, N, O, P: Semantic Segmentation Model, Dynamic Masking & UAVid Evaluation
- Phase Q, R: Bare-Earth DTM Pipeline & H3D DTM Validation
- Phase S, T, U, V, W, X, Y: 10-Minute Benchmark, Profiling, Large-Scale SfM, MVS Chunking
- Phase Z: Final Dataset-Driven Completion Report & Verification Matrix

---

## 2. Verification Plan for Phase A & B

### Automated Unit Tests
- `tests/test_dataset_manifest.py`: Tests provenance manifest generation, hashing, and schema validation.
- `tests/test_canonical_mission_validator.py`: Tests validator on valid canonical missions, detecting timestamp regressions, invalid coordinates, non-normalized quaternions, and malformed CSVs.
- `tests/test_dataset_adapters.py`: Tests adapter conversion logic against deterministic synthetic fixtures for all 6 target datasets.

### Real Sample Verification
- Run adapters on real downloaded subsets for accessible datasets (`MARS-LVIG`, `Zurich MAV`, etc.).
- Validate all generated canonical outputs using `validate_canonical_mission.py`.
- Document conversion statistics in `conversion_report.json` and compile `docs/DATASET_ADAPTER_REPORT.md`.
- Ensure zero regression across the existing test suite (`pytest tests/`, `ruff check .`, `mypy app/`).
