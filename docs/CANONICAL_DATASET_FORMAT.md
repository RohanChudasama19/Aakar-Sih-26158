# Canonical AeroRecon Dataset Format

All external datasets must be converted into this documented canonical mission layout before processing.

## Directory Structure

``
mission/
    video/
        flight.mp4

    frames/
        optional_original_frames/

    telemetry/
        frame_timestamps.csv
        gps.csv
        imu.csv
        barometer.csv
        gimbal.csv
        flight_metadata.json

    calibration/
        camera_intrinsics.json
        camera_imu_extrinsics.json

    gnss/
        rtk_ppk.csv
        rinex/

    control/
        gcps.csv
        checkpoints.csv

    reference/
        lidar.las_or_laz
        dtm.tif
        orthophoto.tif
        trajectory.csv

    semantics/
        images/
        masks/
        classes.json
``

*Not every field is required. Missing data must remain missing. Do not create fake placeholder sensor values.*

## Canonical Schemas

### frame_timestamps.csv
- **frame_index**: int, required, index of the frame in the video/sequence
- **source_timestamp**: float or string, required, original sensor/ROS timestamp
- **canonical_time_s**: float, required, Unix epoch seconds (sub-second precision)
- **video_timestamp_s**: float, optional, time in seconds from the start of the video
- **source_identifier**: string, required, original image filename or ROS topic sequence ID

### gps.csv
- **canonical_time_s**: float, required, Unix epoch seconds
- **lat**: float, required, WGS84 latitude
- **lon**: float, required, WGS84 longitude
- **alt**: float, required, Altitude (specify vertical datum in flight_metadata.json)

### imu.csv
- **canonical_time_s**: float, required, Unix epoch seconds
- **accel_x**, **accel_y**, **accel_z**: float, optional, m/s^2
- **gyro_x**, **gyro_y**, **gyro_z**: float, optional, rad/s
- **q_w**, **q_x**, **q_y**, **q_z**: float, optional, Normalized orientation quaternion

### barometer.csv
- **canonical_time_s**: float, required, Unix epoch seconds
- **pressure**: float, required, hPa or Pascals
- **temperature**: float, optional, Celsius

### rtk_ppk.csv
- **canonical_time_s**: float, required, Unix epoch seconds
- **lat**, **lon**, **height**: float, required
- **quality**: string, required (RTK_FIXED, RTK_FLOAT, DGPS, PPK_FIXED, PPK_FLOAT, GNSS_SINGLE, UNKNOWN)
- **satellite_count**: int, optional
- **sigma_x**, **sigma_y**, **sigma_z**: float, optional, standard deviations

### flight_metadata.json
- **crs**: string, horizontal CRS
- **epsg**: int, EPSG code where applicable
- **vertical_datum**: string (ELLIPSOIDAL, ORTHOMETRIC, LOCAL, UNKNOWN)
- **height_type**: string
- **units**: string

### camera_intrinsics.json
- Standard camera intrinsics matrix and distortion coefficients

### camera_imu_extrinsics.json
- 4x4 Transformation matrix from Camera to IMU frame

### gcps.csv / checkpoints.csv
- **checkpoint_id**: string, required
- **latitude**: float, required
- **longitude**: float, required
- **elevation**: float, required
- **recon_x**, **recon_y**, **recon_z**: float, optional
- **role**: string, required (CONTROL or CHECKPOINT)

## Timestamp Standard
- Canonical internal time is **Unix seconds as float64/sub-second precision**.
- Original timestamps and timebases are preserved.
- Where conversion to Unix is impossible without metadata, a dataset-specific relative epoch is used and explicitly labeled. Do not fabricate Unix time.

## Coordinate Metadata
- Geospatial metadata must record horizontal CRS, EPSG, vertical datum, height type, and units.
- Never convert UNKNOWN automatically.
