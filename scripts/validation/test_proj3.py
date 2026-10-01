import json
import numpy as np
import trimesh
from pathlib import Path
import open3d as o3d
import cv2

work = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AAKAR-SIH26158-Surface-Fix\aakar\data\b3198000-1dd2-4a74-95ee-937f56510279\work")
mesh = trimesh.load(str(work / "dense_balanced" / "fused_CURRENT.ply"))
geo = json.loads((work / "alignment.json").read_text())
sfm = {"poses": {}}
poses = json.loads((work / "poses.json").read_text())
for k, v in poses.items():
    sfm["poses"][int(k)] = np.array(v)

import json
flight = json.loads((work.parent / "inputs" / "flight.json").read_text())
from app.schemas import intrinsics
cam_model = intrinsics(flight, 1600, 900)
K = cam_model.to_matrix()

xyz = mesh.vertices
# Wait, fused_CURRENT.ply is generated from colmap stereo_fusion, which is ALREADY relative!
# I don't need to apply inverse transform to it! It's already in the same frame as sfm["poses"]!
# So just test with it directly.

np.random.seed(42)
pts = np.random.choice(len(mesh.vertices), min(1000, len(mesh.vertices)), replace=False)
tested_points = xyz[pts]

# Let's just project these points and see how many land in front, inside.
in_front = 0
inside = 0

for j, pose in sfm["poses"].items():
    cam = tested_points @ pose[:, :3].T + pose[:, 3]
    p = cam @ K.T
    uv = p[:, :2] / np.maximum(p[:, 2:3], 1e-8)
    
    in_f = (cam[:, 2] > 0)
    in_front += in_f.sum()
    
    ins = (uv[:, 0] >= 1) & (uv[:, 0] < 1599) & (uv[:, 1] >= 1) & (uv[:, 1] < 899)
    ins = ins & in_f
    inside += ins.sum()

print(f"tested points/faces: {len(pts)}")
print(f"in front: {in_front}")
print(f"inside image: {inside}")
print(f"passes occlusion (visible): N/A (tested point cloud)")
print(f"usable views: {inside}")
