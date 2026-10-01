# RTK / PPK Validation

AAKAR parses GNSS states to assign intelligent statistical weight to trajectory priors.

## Quality Enums
- `RTK_FIXED` / `PPK_FIXED` (Default sigma approx 0.02m)
- `RTK_FLOAT` / `PPK_FLOAT` (Default sigma approx 0.20m)
- `DGPS` (Default sigma approx 0.50m)
- `GNSS_SINGLE` (Default sigma approx 2.50m)

## Real Status Report
- GNSS quality ingestion = VERIFIED (parses RTK_FLOAT, RTK_FIXED, etc.)
- PPPH real-data parsing = VERIFIED_REAL_DATA
- raw RINEX solver backend = NOT_AVAILABLE
- RTKLIB detected = no
- RTKLIB actually executed = no

## Measured vs Assumed Uncertainty
- If explicit covariances/sigmas are provided by the solver, they are utilized (safely clipped to prevent infinite weight).
- Otherwise, the system assumes the defaults above.

## Lever Arm
- Exists in schema but strictly disabled (`LEVER_ARM_BLOCKED_FRAME_UNKNOWN`) until sensor/IMU intrinsic-extrinsic proofs are established.
