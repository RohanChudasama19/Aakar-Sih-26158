import sys, json, time, shutil, re
from pathlib import Path
import numpy as np
import trimesh

mesh_ply = trimesh.load('data/mars_hkairport01_quality/work/dense_mars/mesh_raw.ply', process=False)
print(f"mesh_raw.ply faces: {len(mesh_ply.faces)}")

mesh_glb = trimesh.load('demo/mars_hkairport01_quality/mesh.glb', process=False, force='mesh')
total_glb = 0
if hasattr(mesh_glb, 'geometry'):
    for k, v in mesh_glb.geometry.items():
        total_glb += len(v.faces)
        print(f"  {k}: {len(v.faces)} faces")
else:
    total_glb = len(mesh_glb.faces)
print(f"mesh.glb total faces: {total_glb}")
