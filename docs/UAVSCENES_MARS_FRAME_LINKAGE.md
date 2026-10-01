# UAVSCENES / MARS FRAME LINKAGE

## SAMPLEINFOS:
- **entries:** 7199
- **timestamp field:** OriginalImageName (filename prefix)
- **pose fields:** T4x4, P3x3
- **translation:** T4x4 4th column (X, Y, Z)
- **rotation:** T4x4 top-left 3x3
- **pose convention:** T_world_camera (Camera to World)
- **map frame indicated:** Local Cartesian (Z-up), same as cloud_merged.ply

## RTK CSV:
- **rows:** 3900
- **columns:** scenename, headerstamp, lat, lon, alt, easting, northing
- **timestamp range:** 1671606410.009 to 1671607189.909
- **coordinate type:** Geodetic (WGS84) and UTM Zone 50N
- **quality fields:** NONE

## SEQUENCE MATCH:
- **verified:** VERIFIED
- **timestamp residual:** 0.0 sec (overlapping exactly from 1671606440.2 to 1671607160.0)

## RTK PROVENANCE MATCH:
- **verified:** VERIFIED
- **details:** The rtk_positions_raw.csv perfectly matches the Bag GPS lat/lon trajectory but has precise RTK altitude (~100-140m) vs the drifted consumer Bag GPS barometer altitude (~75-120m).

## MAP CLOUD:
- **bounds:** min [-435.03, -289.47, -176.42], max [222.67, 212.12, -37.89]
- **centroid:** [-106.18, -38.67, -107.15]
- **extent:** [657.70, 501.59, 138.53]

## POSE BOUNDS:
- **bounds:** min [-264.52, -164.52, -46.39], max [89.72, 82.32, 1.41]
- **centroid:** [-101.54, -40.06, -0.92]
- **extent:** [354.24, 246.85, 47.80]

## MAP_BOUNDS_OVERLAP: YES

## TRANSFORM CHAIN:
- **available:** FALSE
- **steps:** N/A

## AAKAR_ENU_TO_MAP:
- **possible:** FALSE
- **method:** N/A

## REFERENCE_ALIGNMENT_INDEPENDENT: FALSE

## FRAME_COMPATIBILITY: NOT_VERIFIED

## MISSING INFORMATION:
The sampleinfos_interpolated.json poses exhibit non-rigid SLAM drift (up to ~1.3m) relative to the UTM RTK trajectory. There is no documented exact geodetic datum origin, nor a documented CRS projection parameter string, nor a rigid transformation matrix from WGS84/UTM to the Terra map local frame. A perfectly independent coordinate mapping is impossible without trajectory fitting or ICP.

## NEXT ACTION:
Proceed to use trajectory-based Umeyama alignment or ICP to evaluate relative shape accuracy, since independent absolute CRS evaluation is mathematically impossible.
