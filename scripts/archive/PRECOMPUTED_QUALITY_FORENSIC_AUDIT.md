PRECOMPUTED QUALITY FORENSIC AUDIT

==================================================
1. FORENSIC STAGE COMPARISON (FAILED RUN b83295bd VS BASELINE)
==================================================
- **SFM Extraction & Matching**: Successfully extracted 250 frames (budget limit). Sequential matching worked identically.
- **Sparse Registration**: Registered 244/250 cameras. The 6 missing cameras (000720, 000975, 001125, 001155, 005835, 005895) are isolated dropouts that did NOT fragment the SfM graph (SfM formed a single coherent component).
- **Dense Undistortion**: Here the pipelines materially diverged. 
  - *Baseline*: Undistorted all 244 registered images.
  - *Failed Run*: Undistorted only 103 sparsely sampled images.

==================================================
2. DENSE COLLAPSE ROOT CAUSE INVESTIGATION
==================================================
The severe drop from ~1.47M dense points to 72,266 was caused by a destructive interference between three factors:
1. **The `image_list_path` Bug**: Commit `8bf97f7` inadvertently included two contradictory blocks for Adaptive Dense Reference Selection. The first block forced `image_undistorter` to only output 105 images. This deleted all 145 intermediate frames from the dense workspace, preventing them from being used as stereo source views.
2. **The Outlier Filter Patch**: The experimental `point_filtering` patch and `--GlobalMapper.skip_retriangulation 1` hack heavily pruned the sparse model, removing ~70% of 3D observations.
3. **Loss of Multi-View Support**: Because the intermediate frames were missing, PatchMatch was forced to use wide-baseline images (2-3 frames apart) as source views. Due to the aggressive sparse pruning, these widely-spaced views no longer shared sufficient 3D points. PatchMatch therefore selected almost zero valid source views (e.g. only 2–5 views instead of 20), causing dense triangulation to collapse entirely.

==================================================
3. VIEWER IMPORT ARCHITECTURE REVIEW
==================================================
The current approach of injecting `if jid == "demo-precomputed":` checks directly into core API routes (`/api/jobs/{jid}/download`, `/api/jobs/{jid}/map-data`, etc.) violates production boundaries. It scatters test-specific overrides across the codebase, creating maintenance hazards. 
**Recommendation**: Implement a read-only `DemoMissionProvider` or `ManifestLoader` interface that abstracts the data source. The API routes should remain completely agnostic to whether a job is "live" or "precomputed".

==================================================
4. RELEASE DISCIPLINE CHECK
==================================================
- **HEAD vs rc5**: The latest release tag `v1.1-sih-rc5` remains safely untouched.
- **Files Changed Post-rc5**: `docs/ui_acceptance/*` (screenshots) and `web/*` (UI freeze updates). 
- **Uncommitted Modifications**: Both `app/pipeline/sfm_backend.py` (which contained the aggressive filtering hacks) and `app/main.py` (which contained the viewer hacks) have been reverted to their pristine `rc5` state in the working tree. `app/pipeline/dense_backend.py` has been surgically repaired.

==================================================
5. RECOVERY FIX 
==================================================
1. Reverted `app/pipeline/sfm_backend.py` entirely back to its pristine `rc5` state, restoring full Global BA retriangulation and removing the destructive `point_filtering` step.
2. Surgically patched `app/pipeline/dense_backend.py` to remove the overriding `Block A` of Adaptive Dense Reference Selection. The corrected logic now allows `image_undistorter` to process all 244 valid images (ensuring robust multi-view source support) while correctly using `Block B` to strictly limit `patch-match.cfg` reference views to 105.
This scientifically justified correction restores the high-quality narrow-baseline multi-view support required to hit the ~1.47M target within the 15-minute runtime budget.
