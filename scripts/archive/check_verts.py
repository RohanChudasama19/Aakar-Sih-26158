import trimesh
glb = trimesh.load("data/95f51b12-b771-47bf-9201-c3700f9475a7/work/outputs/model.glb", force='mesh')
print(f"Faces: {len(glb.faces)}, Vertices: {len(glb.vertices)}")
