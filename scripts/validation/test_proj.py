import json
import numpy as np
import trimesh
from pathlib import Path
import open3d as o3d
import cv2

work = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AAKAR-SIH26158-Surface-Fix\aakar\data\b3198000-1dd2-4a74-95ee-937f56510279\work")
mesh = trimesh.load(str(work / "outputs" / "mesh_raw.ply"))
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
if geo["metric_state"] != "RELATIVE":
    xyz = (mesh.vertices - np.array(geo["translation"])) @ np.array(geo["rotation"]) / geo["scale"]

np.random.seed(42)
faces = np.random.choice(len(mesh.faces), 1000, replace=False)
triangles = xyz[mesh.faces[faces]]
centroids = triangles.mean(1)

o3d_mesh = o3d.t.geometry.TriangleMesh()
o3d_mesh.vertex.positions = o3d.core.Tensor(np.asarray(xyz, dtype=np.float32))
o3d_mesh.triangle.indices = o3d.core.Tensor(np.asarray(mesh.faces, dtype=np.uint32))
scene = o3d.t.geometry.RaycastingScene()
scene.add_triangles(o3d_mesh)

in_front = 0
inside = 0
occluded = 0
usable = 0

for j, pose in sfm["poses"].items():
    cam = xyz[mesh.faces[faces]] @ pose[:, :3].T + pose[:, 3]
    p = cam @ K.T
    uv = p[:, :2] / np.maximum(p[:, 2:3], 1e-8)
    
    in_f = (cam[:, 2] > 0).all(1)
    in_front += in_f.sum()
    
    ins = (uv[:, :, 0] >= 1) & (uv[:, :, 0] < 1599) & (uv[:, :, 1] >= 1) & (uv[:, :, 1] < 899)
    ins = ins.all(1) & in_f
    inside += ins.sum()
    
    # raycast
    if ins.any():
        ray_origins = (-pose[:, :3].T @ pose[:, 3]).reshape(1, 3)
        ray_origins = np.repeat(ray_origins, np.sum(ins), axis=0)
        ray_directions = centroids[ins] - ray_origins
        rays = np.concatenate([ray_origins, ray_directions], axis=1).astype(np.float32)
        ans = scene.cast_rays(o3d.core.Tensor(rays))
        index_ray = ans["primitive_ids"].numpy()
        occ = index_ray != faces[ins]
        occluded += occ.sum()
        usable += (~occ).sum()

print(f"tested points/faces: {len(faces)}")
print(f"in front: {in_front}")
print(f"inside image: {inside}")
print(f"passes occlusion (visible): {usable}")
print(f"occluded/missed: {occluded}")
