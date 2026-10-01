AERORECON DISK CLEANUP RESULT

BEFORE:

free space: 2.52 GB

DELETED:

path | bytes recovered | verification
--- | --- | ---
data/test_dense_fix_3 | 5,623,640,024 | Deleted successfully
data/final_fast_quality_demo | 2,331,912,229 | Deleted successfully
data/359de0ec-8706-44ff-954f-fcc14f29a5ff | 2,331,912,426 | Deleted successfully

SKIPPED:

path | reason
--- | ---
N/A | All requested directories met safety conditions and were permanently deleted.

AFTER:

free space: 12.81 GB
actual space recovered: 10.29 GB (10,290,253,824 bytes)

PROTECTED:

active job: INTACT (data/95f51b12-b771-47bf-9201-c3700f9475a7 was not touched)
6-source dense: INTACT (dense_full_ref2/fused.ply, 9,834,889 bytes)
10-source dense: INTACT (dense_10_source_full/fused.ply, 19,963,858 bytes)
6-source mesh: INTACT (dense_full_ref2/mesh_raw.ply, 6,642,285 bytes)
10-source mesh: INTACT (dense_10_source_full/mesh_raw.ply, 5,935,626 bytes)
original inputs: INTACT (demo/fast_quality_demo/video.mp4, 2,331,357,644 bytes)
reports: INTACT
configurations: INTACT

STAGE 2:

potential recovery: 27.87 GB (11.52 GB + 11.52 GB + 4.83 GB)
preservation plan: 
1. DO NOT DELETE ANY FUSED POINT CLOUDS OR MESHES (they are stored outside the stereo folders).
2. DO NOT DELETE configurations (patch-match.cfg, usion.cfg, profile.json).
3. Preserve 3 representative depth/normal map pairs from dense_10_source_full/stereo for scientific evidence (<100 MB).
4. Safely delete the remaining contents of depth_maps/ and 
ormal_maps/ inside dense_full_ref2/stereo, dense_10_source_full/stereo, and dense_fast_quality/stereo.

FINAL:

STAGE_1_COMPLETE = TRUE
ACTIVE_JOB_INTACT = TRUE
SOURCE_CODE_INTACT = TRUE
EVIDENCE_INTACT = TRUE
READY_FOR_STAGE_2 = TRUE

STOP.
