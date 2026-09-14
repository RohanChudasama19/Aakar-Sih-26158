# Surface correction — 14 September 2026

## What was wrong

The baseline triangulated the point cloud in horizontal XY coordinates and discarded long 3D edges. Vertical facades have multiple heights at the same XY position, so this approach can collapse walls and leave disconnected fragments. Both CPU and COLMAP output passed through this mesher. Changing the viewer or uploading more sensor files would not repair this defect.

## Changes

- Replace XY Delaunay with Open3D screened Poisson reconstruction in all three dimensions.
- Remove statistical outliers; estimate normals and orient them toward nearby registered cameras.
- Trim vertices far from measured points and remove tiny disconnected components. This can leave holes; it deliberately does not claim unobserved geometry is measured.
- Retain vertical surfaces, cap the final surface at 60,000 faces, use larger image-atlas tiles, and preserve continuous vertex normals across UV seams.
- Use a matte double-sided PBR material and display surface-connectivity/texture-support status in the result panel.
- Add a regression test that reconstructs a vertical wall whose XY projection is a line.

## Measured real-flight comparison

Input: first 350 frames from the official Zurich urban MAV subset, converted to an 11.667-second undistorted video with the accompanying calibration and GPS. CPU engine, 960-pixel processing width, frame budget 180. No segmentation/depth checkpoint or optional barometer used for this comparison. The budget is a ceiling: motion selection retained 17 frames. Comparison uses the same reconstructed point cloud and cameras.

| Measurement | Original | Corrected |
|---|---:|---:|
| Registered cameras | 17 / 17 | 17 / 17 |
| Input 3D points | 38,083 | 38,083 |
| Output triangles | 3,082 | 60,000 |
| Connected surface components | 796 | 7 |
| Largest component / total triangle area | 15.38% | 99.50% |

The corrected surface has image projections for about 99.49% of faces. That statistic does not establish visibility, correct depth or correct texture. Triangle count and connectivity are not accuracy metrics. Poisson interpolates new geometry between observed points.

The full corrected CPU run took 46.609 seconds in this environment; it is not a ten-minute/GPU benchmark. A later GLB-only refresh preserved continuous vertex normals. The GPS similarity fit returned a residual of 0.766 m, but this is NOT an independently measured spatial error; the source GPS uncertainty and short trajectory make metric interpretation weak.

**Visual inspection: the building is recognizable from the camera-facing view, but holes, warped walls, vegetation noise, texture seams and incomplete surfaces remain. The realism requirement is NOT met.** This patch fixes the horizontal-meshing defect; it does not complete a production-quality photogrammetry pipeline.

`docs/surface-evidence/before.png` and `after.png` show actual WebGL renders from the same recovered camera, with identical lighting. They are not generated illustrations. This is a favorable observed view; other views expose additional missing surfaces. The result archive includes the corrected GLB, report and reference metadata for independent inspection.

## Tests

- Full suite: 11 passed, two upstream deprecation warnings.
- Vertical-wall test checks width, height, plane deviation and connectivity.
- End-to-end test executes all stages and reopens GLB, PLY, LAS and GeoTIFF; it does not certify visual quality.
- JavaScript syntax and Python compilation passed.
- Before/after GLBs loaded and rendered in headless Chromium without page errors.
- Docker, CUDA/COLMAP, optional checkpoint inference and surveyed accuracy remain unvalidated here.

The old sample report, sample-result ZIP and earlier screenshots are historical baseline artifacts, as noted in VALIDATION.md.

## Apply and rerun

Extract this update into a new folder. Stop the old server before starting the replacement. Preserve old data separately if you need its jobs.

Docker: run `docker compose up --build` inside the new `aerorecon` folder. Rebuild is required for Open3D. Docker startup was not tested here.

Local Windows: run `.\.venv\Scripts\python -m pip install -r requirements.txt` in an existing compatible virtual environment, then `.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. For a new environment follow README.md.

Local Linux/macOS: run `.venv/bin/python -m pip install -r requirements.txt`, then `.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.

Submit a NEW mission using the video, matching GPS/metadata and the matching intrinsics JSON. Old exported models do not change. For the Zurich clip retain budget 180; increasing it alone does not recover missing viewpoints.

## Work still required for a realistic result

The CPU pose solver has no global bundle adjustment; dense stereo remains a limited baseline. Next engineering work is to evaluate the supplied COLMAP mapping/PatchMatch path on an NVIDIA GPU with this revised mesher, add visibility-aware texture selection and seam blending, and evaluate distortion/pose/depth accuracy on a longer capture. It is not valid to promise a photorealistic result merely by selecting CUDA.

A new capture should observe the desired walls and roof from overlapping, translating viewpoints with sharp imagery and correct camera calibration. The 11.7-second subset does not show a complete building. IMU remains archived only. Segmentation can remove moving objects; RTK can help position alignment. Neither creates missing surface observations, and the optional ONNX path does not fuse inferred points into the measured mesh.

Sources: [Zurich urban MAV dataset](https://rpg.ifi.uzh.ch/zurichmavdataset.html), [Open3D surface reconstruction](https://www.open3d.org/docs/release/tutorial/geometry/surface_reconstruction.html), [COLMAP tutorial](https://colmap.github.io/tutorial.html).
