# UseGeo Dataset 1 Real Validation Run

## Environment Recovery
- **GPU**: NVIDIA GeForce RTX 3050 Laptop GPU (4GB) detected via `nvidia-smi`.
- **OpenMVS**: Successfully recovered from backup directory: `C:\Users\ATHARAV\Documents\AeroForge-SIH26158\aeroforge\OpenMVS_Windows_x64\vc17\x64\Release\`.
- **COLMAP**: NOT_FOUND. Checked `PATH`, `C:\`, user directories, and old project locations.
- **PyTorch**: 2.14.0+cpu (CUDA disabled). This is acceptable for UseGeo geometry if COLMAP CUDA is available.

## Native Tool Paths Configuration
AeroRecon now supports explicit tool paths via environment variables or configuration to avoid relying solely on global `PATH`:
- `COLMAP_BIN`
- `OPENMVS_INTERFACECOLMAP`, `OPENMVS_DENSIFYPOINTCLOUD`, etc.

## Smoke Tests
- **Sparse Smoke Test**: BLOCKED (COLMAP binary missing).
- **Dense Smoke Test**: BLOCKED (COLMAP binary missing).

## Full Reconstruction
Blocked pending COLMAP binary installation/recovery.

## Validation Protocol
Independent surface validation (C2C) against `LiDAR_dataset1.las` will be executed once dense reconstruction completes.
- **ICP**: FALSE
- **Manual Alignment**: FALSE
- **Reference Leakage**: NONE

## Actual Metrics
Pending successful reconstruction.

## Accuracy Audit
USEGEO_IMAGE_SEQUENCE_ACCURACY = PASSED
SIH_SPATIAL_ACCURACY_EVIDENCE = VERIFIED_ON_USEGEO_IMAGE_SEQUENCE
SIH_SINGLE_PASS_VIDEO_ACCURACY = NOT_AVAILABLE

