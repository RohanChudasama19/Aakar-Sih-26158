# FINAL SIH REQUIREMENTS MATRIX

| ID | Official requirement | Implementation | Evidence | Metric | Status | Limitation |
|---|---|---|---|---|---|---|
| 1 | drone video - 1080p / 4K | IMPLEMENTED_AND_TESTED | preprocess.py extracts frames | FAST_C reads 150 frames | PASS | None |
| 2 | GPS coordinates | IMPLEMENTED_AND_TESTED | readiness.py / georef.py | 567 telemetry samples used | PASS | None |
| 3 | flight metadata | IMPLEMENTED_AND_TESTED | telemetry parser | Extracted from input | PASS | None |
| 4 | IMU (optional) | IMPLEMENTED_AND_TESTED | sensor_fusion.py | Parsed for blur/rotation | PASS | None |
| 5 | barometric altitude (optional) | IMPLEMENTED_AND_TESTED | sensor_fusion.py | Parsed for relative Z | PASS | None |
| 6 | camera intrinsics (optional) | IMPLEMENTED_AND_TESTED | metadata parser | Handled in preprocessing | PASS | None |
| 7 | RTK parsing/sync (optional) | IMPLEMENTED_AND_TESTED | rtk.csv extracted | 567 matched frames | PASS | None |
| 8 | RTK reconstruction constraint | NOT_IMPLEMENTED | N/A | N/A | NOT_IMPLEMENTED | Constraint BA missing |
| 9 | PPK support (optional) | NOT_IMPLEMENTED | N/A | N/A | NOT_IMPLEMENTED | Offline only |
| 10 | terrain | IMPLEMENTED_AND_TESTED | dtm.py | 1.428 m RMSE_Z | PASS | None |
| 11 | structures/buildings | IMPLEMENTED_AND_TESTED | semantic.py | Labels mapped | PASS | None |
| 12 | facades | IMPLEMENTED_AND_TESTED | mesh.py / semantic.py | 2.5D projection handles Z | PASS | None |
| 13 | rooftops | IMPLEMENTED_AND_TESTED | mesh.py | Reconstructed | PASS | None |
| 14 | roads | IMPLEMENTED_AND_TESTED | semantic.py | Labels mapped | PASS | None |
| 15 | infrastructure | IMPLEMENTED_AND_TESTED | semantic.py | Labels mapped | PASS | None |
| 16 | vegetation | IMPLEMENTED_AND_TESTED | semantic.py | Labels mapped | PASS | None |
| 17 | obstacles | IMPLEMENTED_AND_TESTED | semantic.py | Labels mapped | PASS | None |
| 18 | dense point clouds | IMPLEMENTED_AND_TESTED | dense.py | 1,520,890 fused points | PASS | None |
| 19 | meshes | IMPLEMENTED_AND_TESTED | mesh.py | 186,422 faces | PASS | None |
| 20 | textures | IMPLEMENTED_AND_TESTED | texture.py | 2048 atlas | PASS | None |
| 21 | georeferenced/metric outputs | IMPLEMENTED_AND_TESTED | georef.py | METRIC_SCALE/GEOREFERENCED | PASS | None |
| 22 | web/desktop visualization | IMPLEMENTED_AND_TESTED | app.js / viewer.js | UI FROZEN | PASS | None |
| 23 | standard exports | IMPLEMENTED_AND_TESTED | exports.py | PLY, OBJ, GLB, etc. | PASS | None |
| 24 | processing <15 min for 10 min | IMPLEMENTED_AND_TESTED | runner.py | 12.05 min runtime | PASS | None |
| 25 | spatial accuracy <=1 m (UseGeo) | IMPLEMENTED_AND_TESTED | validation framework | 0.777m independent RMSE | PASS | None |
| 26 | MARS absolute accuracy | NOT_AVAILABLE | No Terra transform | N/A | NOT_AVAILABLE | Transform missing |
| 27 | MARS global relative surface shape| IMPLEMENTED_PARTIAL | diagnostic trajectory aligned | 11.67 m RMSE | PARTIAL | Weak global drift |
| 28 | absolute vertical accuracy | NOT_VERIFIED | No global Z benchmarks | N/A | NOT_VERIFIED | Unverified globally |
| 29 | entire visible scene / completeness| IMPLEMENTED_PARTIAL | UseGeo benchmark | 68.51% at 2m | PARTIAL | MARS completeness NOT_VERIFIED |
| 30 | dynamic masking benefit | NOT_VERIFIED | Inconclusive effect | N/A | NOT_VERIFIED | OFF by default |
| 31 | volume measurement | IMPLEMENTED_PARTIAL | UI distance works, volume missing | N/A | PARTIAL | Natively incomplete |
