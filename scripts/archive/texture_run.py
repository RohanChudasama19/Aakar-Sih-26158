import json
import trimesh
from pathlib import Path
import numpy as np

from app.pipeline.texture import texture_mesh

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
mesh_repaired = work_dir / "dense_10_source_full/mesh_repaired.ply"

geo = json.loads((work_dir / "alignment.json").read_text())
poses = json.loads((work_dir / "poses.json").read_text())

f = 2158.4545858578222
cx = 1920
cy = 1080

scale = 1600.0 / 3840.0
k = np.array([
    [f * scale, 0, cx * scale],
    [0, f * scale, cy * scale],
    [0, 0, 1]
])

poses_np = {k: np.array(v) for k, v in poses.items()}
sfm = {"poses": poses_np}

# Complete Degraded Reconstruction
mesh = trimesh.load(str(mesh_repaired))
print("Texturing Complete Mesh...")
options = {"occlusion_test": True}
tex_mesh = texture_mesh(mesh, geo, sfm, k, work_dir / "dense_10_source_full/images", options)
print(tex_mesh.metadata)
tex_mesh.export(str(work_dir / "dense_10_source_full/mesh_textured.glb"))

# Largest Component Preview
print("Texturing Largest Component...")
import open3d as o3d
mesh_o3d = o3d.io.read_triangle_mesh(str(mesh_repaired))
cc_indices, cc_counts, _ = mesh_o3d.cluster_connected_triangles()
largest_c = np.argmax(cc_counts)
mesh_o3d.remove_triangles_by_mask(np.asarray(cc_indices) != largest_c)
mesh_o3d.remove_unreferenced_vertices()

preview = trimesh.Trimesh(vertices=np.asarray(mesh_o3d.vertices), faces=np.asarray(mesh_o3d.triangles))
tex_preview = texture_mesh(preview, geo, sfm, k, work_dir / "dense_10_source_full/images", options)
print("Preview report:")
print(tex_preview.metadata)
tex_preview.export(str(work_dir / "dense_10_source_full/largest_component_textured.glb"))
tex_preview.export(str(work_dir / "dense_10_source_full/largest_component_textured.ply"))

