# AAKAR User Guide

## Dashboard
The main screen lists all missions (completed, failed, or running). 
The top bar indicates whether the background worker is online. If offline, missions will queue but not start.

## Creating a Mission
1. Click **New Mission**.
2. **Video:** Must be a clear, non-blurry flight video (MP4/MOV) with changing viewpoints.
3. **GPS CSV:** Telemetry containing columns lat, lon, alt, time.
4. **Flight JSON:** Metadata describing drone parameters.
5. Choose your engine: **CPU** (fast but low detail) or **CUDA** (requires NVIDIA GPU, high detail).
6. Click **Start**.

## Mission Workspace
While running, progress streams live via SSE. If a failure occurs, the log will turn red with troubleshooting steps.
- **Cancel:** You can cancel a running job at any time. This terminates the subprocesses safely.
- **Retry:** If a job fails or is cancelled, use Retry to restart from a clean slate.

## 3D Viewer & Tools
Once complete, the mission opens in an interactive 3D viewer.
- **Visual Modes:** Toggle between Textured, Dense, Mesh, Semantic, etc.
- **Measurements:** Click the ruler icon to measure 3D distances or planar areas. (Measurements are metric if GPS alignment succeeded).
- **Map View:** Toggle to the 2D map to see the trajectory.

## Exporting
Click the **Download Zip** button to receive the full package of standardized deliverables: .ply, .obj, .las, .gltf, .glb, .tif (and .fbx if Blender is configured on the server).
