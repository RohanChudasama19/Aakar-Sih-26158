import json
import trimesh
import numpy as np

glb = trimesh.load("demo/mars_hkairport01_quality/mesh.glb", process=False, force='mesh')
if hasattr(glb, 'geometry'):
    geom = next(iter(glb.geometry.values()))
else:
    geom = glb

uvs = geom.visual.uv
if uvs is None:
    print("No UVs found!")
else:
    u = uvs[:, 0]
    v = uvs[:, 1]
    u_invalid = (u < 0) | (u > 1)
    v_invalid = (v < 0) | (v > 1)
    invalid = u_invalid | v_invalid
    print(f"Total UVs: {len(uvs)}")
    print(f"Invalid UVs (<0 or >1): {invalid.sum()} ({invalid.sum()/len(uvs)*100:.2f}%)")
    print(f"U bounds: [{u.min():.5f}, {u.max():.5f}]")
    print(f"V bounds: [{v.min():.5f}, {v.max():.5f}]")
