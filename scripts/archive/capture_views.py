import open3d as o3d
from pathlib import Path
import os
import json
import numpy as np

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
mesh_6_path = work_dir / "dense_full_ref2/mesh_raw.ply"
mesh_10_path = work_dir / "dense_10_source_full/mesh_raw.ply"
ply_6_path = work_dir / "dense_full_ref2/fused.ply"

out_dir = Path("screenshots")
out_dir.mkdir(exist_ok=True)

def render_mesh(path, out_file):
    if not path.exists(): return
    mesh = o3d.io.read_triangle_mesh(str(path))
    mesh.compute_vertex_normals()
    vis = o3d.visualization.Visualizer()
    vis.create_window(visible=False, width=1920, height=1080)
    vis.add_geometry(mesh)
    opt = vis.get_render_option()
    opt.mesh_show_back_face = True
    opt.background_color = np.asarray([1.0, 1.0, 1.0])
    
    vis.poll_events()
    vis.update_renderer()
    vis.capture_screen_image(str(out_file))
    vis.destroy_window()

def render_pc(path, out_file):
    if not path.exists(): return
    pc = o3d.io.read_point_cloud(str(path))
    vis = o3d.visualization.Visualizer()
    vis.create_window(visible=False, width=1920, height=1080)
    vis.add_geometry(pc)
    opt = vis.get_render_option()
    opt.point_size = 2.0
    opt.background_color = np.asarray([1.0, 1.0, 1.0])
    
    vis.poll_events()
    vis.update_renderer()
    vis.capture_screen_image(str(out_file))
    vis.destroy_window()

render_mesh(mesh_6_path, out_dir / "mesh_6.png")
render_mesh(mesh_10_path, out_dir / "mesh_10.png")
render_pc(ply_6_path, out_dir / "pc_6.png")
render_pc(work_dir / "dense_10_source_full/fused.ply", out_dir / "pc_10.png")

print(f"Screenshots saved to {out_dir.resolve()}")
