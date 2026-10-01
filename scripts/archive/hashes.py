import open3d as o3d
from pathlib import Path
import json

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
ply_6 = work_dir / "dense_full_ref2/fused.ply"
mesh_6 = work_dir / "dense_full_ref2/mesh_raw.ply"
ply_10 = work_dir / "dense_10_source_full/fused.ply"
mesh_10 = work_dir / "dense_10_source_full/mesh_raw.ply"

import hashlib
def sha256(path):
    if not path.exists(): return "Missing"
    return hashlib.sha256(path.read_bytes()).hexdigest()

print(f"6-source ply: {ply_6.stat().st_size} bytes, {sha256(ply_6)}")
print(f"6-source mesh: {mesh_6.stat().st_size} bytes, {sha256(mesh_6)}")
print(f"10-source ply: {ply_10.stat().st_size} bytes, {sha256(ply_10)}")
print(f"10-source mesh: {mesh_10.stat().st_size} bytes, {sha256(mesh_10)}")
