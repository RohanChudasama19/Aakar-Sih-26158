import trimesh
import numpy as np

glb_path = "data/mars_hkairport01_quality/work/outputs/model.glb"
ply_path = "demo/mars_hkairport01_quality/mesh.ply"

glb = trimesh.load(glb_path, force='mesh')
ply = trimesh.load(ply_path)

print(f"GLB faces: {len(glb.faces)}")
print(f"PLY faces: {len(ply.faces)}")

if len(glb.faces) == len(ply.faces):
    # Check bounding box
    print(f"GLB Bounds: {glb.bounds}")
    print(f"PLY Bounds: {ply.bounds}")
    
    # Check first few face centroids to see if triangle ordering is identical
    glb_c = glb.triangles_center
    ply_c = ply.triangles_center
    
    diff = np.linalg.norm(glb_c[:10] - ply_c[:10], axis=1)
    print(f"Centroid diff for first 10 faces: {diff}")
    
    max_diff = np.max(np.linalg.norm(glb_c - ply_c, axis=1))
    print(f"Max centroid difference across all faces: {max_diff}")
    
    if max_diff < 1e-4:
        print("Triangle ordering and geometry are EXACTLY matched!")
    else:
        print("Mismatched ordering or coordinate transform!")
else:
    print("Face counts differ!")
