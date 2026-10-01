import open3d as o3d
import numpy as np
from pathlib import Path

exp_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work/dense_experiment")

mesh_min4 = o3d.io.read_triangle_mesh(str(exp_dir / "mesh_min4.ply"))
mesh_min2 = o3d.io.read_triangle_mesh(str(exp_dir / "mesh_min2.ply"))

# Compute normals for visualization
mesh_min4.compute_vertex_normals()
mesh_min2.compute_vertex_normals()

# Add a fake color if needed, or let open3d render it
mesh_min4.paint_uniform_color([0.8, 0.8, 0.8])
mesh_min2.paint_uniform_color([0.8, 0.8, 0.8])

vis = o3d.visualization.Visualizer()
vis.create_window(visible=False, width=1280, height=720)
vis.add_geometry(mesh_min4)
vis.poll_events()
vis.update_renderer()
vis.capture_screen_image(str(exp_dir / "screenshot_min4.png"))
vis.destroy_window()

vis = o3d.visualization.Visualizer()
vis.create_window(visible=False, width=1280, height=720)
vis.add_geometry(mesh_min2)
vis.poll_events()
vis.update_renderer()
vis.capture_screen_image(str(exp_dir / "screenshot_min2.png"))
vis.destroy_window()
