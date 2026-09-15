# Phase 4 Completion Report: Sensor Fusion, Metric Scaling, and Georeferencing

## Accomplishments
The objective of Phase 4 was to introduce an explicitly traced metric/geospatial alignment layer supporting synchronized telemetry for accurate visual scaling, replacing the naive `frame` count interpolation with true timestamps, and demarcating control from verification (checkpoints).

### 1. Unified Metric State Model
- Replaced the opaque boolean `valid` flag with an explicit `MetricState` enumeration:
  - `RELATIVE`: The reconstruction is unscaled (e.g., stationary GPS, insufficient data).
  - `METRIC_SCALE`: Measurements are to scale but absolute orientation/coordinates are unknown.
  - `GEOREFERENCED_METRIC`: Model is both metrically scaled and aligned to WGS84 coordinates.
- Prevented exporting geographic data (GeoTIFF, LAS) unless the `MetricState` is explicitly `GEOREFERENCED_METRIC`.
- Modified `report.json` and `report.txt` outputs to clearly declare "GPS alignment residual" as a distinct fit measurement, ensuring it is *not* represented as independent ground-truth accuracy.

### 2. Time-Based Telemetry Synchronization
- Deprecated interpolating sensor values directly onto sequential video frames.
- Re-architected `runner.py` and `georef.py` to extract `start_time_utc` from metadata.
- Frame alignments are now mapped strictly using `time_sec` elapsed combined with absolute GPS timestamps, allowing fluctuating frame rates or telemetry delays to be addressed robustly.

### 3. Coordinate Systems
- Established absolute metrics via `pyproj` transformation from WGS84 (Latitude, Longitude) into standard UTM Cartesian planes for accurate scale extraction, overriding previous raw projections.
- Output models and exports trace back explicitly to `EPSG` origins. `geo["origin"]` holds exactly the UTM shift required by standard LAS formats.

### 4. Sim(3) Camera Adjustments
- Re-implemented RANSAC Umeyama algorithm to ensure robustness against GPS outliers.
- `georef.py` now transforms the `SfM` bundle cameras *in-place*. Downstream meshing routines receive completely georeferenced coordinates from the origin rather than computing offsets late in the pipeline.
- Established the `checkpoint_rmse_3d` parameter ready to ingest separated independent ground control points without polluting the RANSAC fit itself.

### Verification
- Authored explicit tests inside `test_georef.py` covering degenerate cases, absolute similarity alignment accuracy, and coordinate bounds.
- Validated end-to-end CPU pipeline test `test_pipeline.py`, proving integration success. All 32 repository tests pass safely.
