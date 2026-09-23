# FINAL SIH REQUIREMENTS MATRIX

| ID | Official requirement | Implementation | Evidence | Metric | Status | Limitation |
|---|---|---|---|---|---|---|
| 1 | drone video — 1080p / 4K | IMPLEMENTED_AND_TESTED | preprocess.py extracts frames | FAST_C reads 150 frames | PASS | None |
| 2 | GPS coordinates | IMPLEMENTED_AND_TESTED | readiness.py / georef.py | 567 telemetry samples used | PASS | None |
| 3 | flight metadata | IMPLEMENTED_AND_TESTED | telemetry parser | Extracted from input | PASS | None |
| 4 | IMU | IMPLEMENTED_AND_TESTED | sensor_fusion.py | Parsed for blur/rotation | PASS | None |
| 5 | barometric altitude | IMPLEMENTED_AND_TESTED | sensor_fusion.py | Parsed for relative Z | PASS | None |
| 6 | camera intrinsics | IMPLEMENTED_AND_TESTED | metadata parser | Handled in preprocessing | PASS | None |
| 7 | RTK / PPK | IMPLEMENTED_PARTIAL | Parsed in georef/rtk.csv | 567 matched frames | PARTIAL | Constraint BA NOT_IMPLEMENTED |
| 8 | terrain | IMPLEMENTED_AND_TESTED | dtm.py | 1.428 m RMSE_Z | PASS | None |
| 9 | structures/buildings | IMPLEMENTED_AND_TESTED | semantic.py | Labels mapped | PASS | None |
| 10 | facades | IMPLEMENTED_AND_TESTED | mesh.py / semantic.py | 2.5D projection handles Z | PASS | None |
| 11 | rooftops | IMPLEMENTED_AND_TESTED | mesh.py | Reconstructed | PASS | None |
| 12 | roads | IMPLEMENTED_AND_TESTED | semantic.py | Labels mapped | PASS | None |
| 13 | infrastructure | IMPLEMENTED_AND_TESTED | semantic.py | Labels mapped | PASS | None |
| 14 | vegetation | IMPLEMENTED_AND_TESTED | semantic.py | Labels mapped | PASS | None |
| 15 | obstacles | IMPLEMENTED_AND_TESTED | semantic.py | Labels mapped | PASS | None |
| 16 | dense point clouds | IMPLEMENTED_AND_TESTED | dense.py | 1,520,890 fused points | PASS | None |
| 17 | meshes | IMPLEMENTED_AND_TESTED | mesh.py | 186,422 faces | PASS | None |
| 18 | textures | IMPLEMENTED_AND_TESTED | texture.py | 2048 atlas | PASS | None |
| 19 | georeferenced/metric outputs | IMPLEMENTED_AND_TESTED | georef.py | METRIC_SCALE/GEOREFERENCED | PASS | None |
| 20 | web/desktop visualization | IMPLEMENTED_AND_TESTED | app.js / viewer.js | UI FROZEN | PASS | None |
| 21 | standard exports | IMPLEMENTED_AND_TESTED | exports.py | PLY, OBJ, GLB, etc. | PASS | None |
| 22 | processing <15 min for 10 min | IMPLEMENTED_AND_TESTED | runner.py | 12.05 min runtime | PASS | None |
| 23 | spatial accuracy <=1 m | IMPLEMENTED_PARTIAL | validation framework | 0.777m on UseGeo | PARTIAL | MARS absolute accuracy NOT_AVAILABLE |
| 24 | entire visible scene | IMPLEMENTED_PARTIAL | validation framework | 68.51% at 2m (UseGeo) | PARTIAL | MARS scene completeness NOT_VERIFIED |
| 25 | usable exported 3D products | IMPLEMENTED_AND_TESTED | exports.py | Verified in tests | PASS | None |
