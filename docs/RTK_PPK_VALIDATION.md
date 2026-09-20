# RTK / PPK Validation

AeroRecon parses GNSS states to assign intelligent statistical weight to trajectory priors.

## Quality Enums
- `RTK_FIXED` / `PPK_FIXED` (Default sigma approx 0.02m)
- `RTK_FLOAT` / `PPK_FLOAT` (Default sigma approx 0.20m)
- `DGPS` (Default sigma approx 0.50m)
- `GNSS_SINGLE` (Default sigma approx 2.50m)

## Measured vs Assumed Uncertainty
- If explicit covariances/sigmas are provided by the solver, they are utilized (safely clipped to prevent infinite weight).
- Otherwise, the system assumes the defaults above.

## Raw RINEX Solver Strategy
- `RAW_RINEX_SOLVING = NOT_AVAILABLE`
- Direct RINEX computation via RTKLIB or similar is not currently integrated as an onboard process.
- We ingest the outputs (like `.pos` files or parsed corrections) rather than solving locally.

## Real PPPH-UAV Status
- Real ingestion paths are validated.
- Contains `.obs`, `.bia`, `.clk`, `.sp3`, and `.atx` files.

## Lever Arm
- Exists in schema but strictly disabled (`LEVER_ARM_BLOCKED_FRAME_UNKNOWN`) until sensor/IMU intrinsic-extrinsic proofs are established.
