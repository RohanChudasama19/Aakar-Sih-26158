import sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

# Verify texture metadata from the successful run
import trimesh, numpy as np
glb = trimesh.load("data/mars_hkairport01_quality/work/dense_mars/mesh_textured.glb", process=False, force='mesh')
if hasattr(glb, 'geometry'):
    total_verts = sum(len(v.vertices) for v in glb.geometry.values())
    total_faces = sum(len(v.faces) for v in glb.geometry.values())
    print(f"GLB geometries: {len(glb.geometry)}")
    for k, v in glb.geometry.items():
        print(f"  [{k}] verts={len(v.vertices):,} faces={len(v.faces):,}")
        if hasattr(v.visual, 'uv') and v.visual.uv is not None:
            uv = v.visual.uv
            valid_uv = np.all((uv >= 0) & (uv <= 1), axis=1).sum()
            print(f"    UV: {uv.shape} valid(0-1)={valid_uv:,}/{len(uv):,}")
        if hasattr(v.visual, 'material') and v.visual.material is not None:
            mat = v.visual.material
            print(f"    Material: {mat.__class__.__name__}")
            if hasattr(mat, 'image') and mat.image is not None:
                print(f"    Atlas: {mat.image.size}")
else:
    print(f"Flat mesh: verts={len(glb.vertices):,} faces={len(glb.faces):,}")

# Get texture coverage from the last texture run
# The texture backend outputs textured_face_fraction in metadata
# Let's probe the actual textured face count
print()
print("--- Texture Coverage ---")
# Load mesh_raw (before texturing) vs mesh_textured face counts
raw = trimesh.load("data/mars_hkairport01_quality/work/dense_mars/mesh_raw.ply", process=False)
print(f"Original faces:  {len(raw.faces):,}")
if hasattr(glb, 'geometry'):
    total_tex_faces = sum(len(v.faces) for v in glb.geometry.values())
    print(f"Textured faces:  {total_tex_faces:,}")
    print(f"Texture coverage: ~{total_tex_faces/len(raw.faces)*100:.1f}%")
