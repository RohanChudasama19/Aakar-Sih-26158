import open3d as o3d
import numpy as np

mesh = o3d.geometry.TriangleMesh.create_sphere()
mesh.compute_vertex_normals()

try:
    vis = o3d.visualization.Visualizer()
    vis.create_window(visible=False)
    vis.add_geometry(mesh)
    vis.poll_events()
    vis.update_renderer()
    img = vis.capture_screen_float_buffer(False)
    print("Screen capture successful")
except Exception as e:
    print(f"Failed: {e}")
