# Sensor Fusion Architecture

AeroRecon enforces strict separation between visual estimation geometry and prior constraints to maintain mathematically defensible local-metric consistency.

## Phase E1: Frame-Agnostic Fusion
Extracts useful constraints that do not depend on unresolved hardware orientation frames.

1. **GNSS Prior Weighing:** Inverse-variance projection via RANSAC robust alignment. Uses `RTK_FIXED`, `DGPS`, etc., mapping to deterministic sigmas.
2. **Barometer Trend:** Simple exponential pressure modeling tied to initial baseline reference pressure. Resolves relative height.
3. **Motion Magnitude Scoring:** Penalizes photogrammetry weights via scalar $|a|$ and $|\omega|$, reducing selection probability of severely motion-blurred images or extreme vibrations safely.

## Phase E2: Orientation Fusion (BLOCKED)
Currently barred by strict safety rules due to missing external intrinsic-extrinsic proof for available datasets.
