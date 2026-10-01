import json
import trimesh
import numpy as np
from pathlib import Path
import open3d as o3d
from app.pipeline.georef import transform

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
ply_10 = work_dir / "dense_10_source_full/fused.ply"
mesh_10 = work_dir / "dense_10_source_full/mesh_raw.ply"
mesh_repaired = work_dir / "dense_10_source_full/mesh_repaired.ply"
sparse = work_dir / "sparse.npz"

geo = json.loads((work_dir / "alignment.json").read_text())

def print_bbox(name, pts):
    pts = np.asarray(pts)
    bbox_min, bbox_max = pts.min(axis=0), pts.max(axis=0)
    extents = bbox_max - bbox_min
    extent_norm = np.linalg.norm(extents)
    print(f"{name}:")
    print(f"  Min: [{bbox_min[0]:.2f}, {bbox_min[1]:.2f}, {bbox_min[2]:.2f}]")
    print(f"  Max: [{bbox_max[0]:.2f}, {bbox_max[1]:.2f}, {bbox_max[2]:.2f}]")
    print(f"  Extents: {extents[0]:.2f} x {extents[1]:.2f} x {extents[2]:.2f}")
    print(f"  Diagonal: {extent_norm:.2f}")

# 1. Sparse cloud
sp = np.load(str(sparse))["points"]
print_bbox("1. Sparse PLY (COLMAP)", sp)

# 2. Raw fused PLY
pc = trimesh.load(str(ply_10))
xyz = np.asarray(pc.vertices)
print_bbox("2. Raw fused PLY (COLMAP)", xyz)

# 3. Mesher input (local ENU)
local = transform(xyz, geo)
print_bbox("3. Mesher input (ENU)", local)

print(f"\nGeoref scale: {geo['scale']:.2f}")
print(f"Georef origin: {geo['origin']}")

# 4. Trimmed mesh
if mesh_10.exists():
    m10 = trimesh.load(str(mesh_10))
    print_bbox("5. Original Trimmed Mesh (ENU)", m10.vertices)

if mesh_repaired.exists():
    m_rep = trimesh.load(str(mesh_repaired))
    print_bbox("5b. Repaired Trimmed Mesh (ENU)", m_rep.vertices)

