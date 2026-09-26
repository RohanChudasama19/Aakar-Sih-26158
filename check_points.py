import trimesh
pc = trimesh.load("data/95f51b12-b771-47bf-9201-c3700f9475a7/work/dense_fast_quality/fused.ply")
print("Fused PLY points:", len(pc.vertices))
