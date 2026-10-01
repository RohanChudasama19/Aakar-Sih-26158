import trimesh
import json
import os

def analyze(name, glb_path, ply_path):
    print(f"--- {name} ---")
    try:
        glb = trimesh.load(glb_path, force='mesh')
        ply = trimesh.load(ply_path)
        print(f"GLB - vertices: {len(glb.vertices)}, faces: {len(glb.faces)}")
        print(f"PLY - vertices: {len(ply.vertices)}, faces: {len(ply.faces)}")
        if len(glb.faces) == len(ply.faces):
            print("Face counts match! Checking ordering...")
            # We can check area or centroid of a few faces to confirm order
            if len(glb.faces) > 0:
                print(f"GLB Face 0: {glb.faces[0]}, PLY Face 0: {ply.faces[0]}")
        else:
            print("Face counts differ!")
    except Exception as e:
        print(f"Error: {e}")

analyze(
    "MARS", 
    "demo/mars_hkairport01_quality/mesh.glb", 
    "demo/mars_hkairport01_quality/mesh.ply"
)
analyze(
    "Colorado", 
    "data/95f51b12-b771-47bf-9201-c3700f9475a7/work/outputs/model.glb",
    "data/95f51b12-b771-47bf-9201-c3700f9475a7/work/outputs/mesh_analysis.ply"
)
