import open3d as o3d
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
mesh_repaired = work_dir / "dense_10_source_full/mesh_repaired.ply"

mesh = o3d.io.read_triangle_mesh(str(mesh_repaired))
mesh.compute_vertex_normals()

# Screen capture complete mesh
vis = o3d.visualization.Visualizer()
vis.create_window(visible=False, width=800, height=600)
vis.add_geometry(mesh)
vis.poll_events()
vis.update_renderer()
img = np.asarray(vis.capture_screen_float_buffer(False))
plt.imsave("complete_mesh.png", img)
vis.destroy_window()

# Screen capture largest component
cc_indices, cc_counts, _ = mesh.cluster_connected_triangles()
largest_c = np.argmax(cc_counts)
largest_mesh = mesh.select_by_index(np.where(np.asarray(cc_indices) == largest_c)[0])

vis = o3d.visualization.Visualizer()
vis.create_window(visible=False, width=800, height=600)
vis.add_geometry(largest_mesh)
vis.poll_events()
vis.update_renderer()
img = np.asarray(vis.capture_screen_float_buffer(False))
plt.imsave("largest_component.png", img)
vis.destroy_window()

print("Screenshots saved.")
