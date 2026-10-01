import open3d as o3d
import numpy as np
from pathlib import Path
from PIL import Image

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
mesh_repaired = work_dir / "dense_10_source_full/mesh_repaired.ply"

mesh = o3d.io.read_triangle_mesh(str(mesh_repaired))
mesh.compute_vertex_normals()

# Setup view
def render(geometry, filename):
    vis = o3d.visualization.Visualizer()
    vis.create_window(visible=False, width=1280, height=720)
    vis.add_geometry(geometry)
    
    # Adjust view
    ctr = vis.get_view_control()
    ctr.set_front([0.0, -1.0, -1.0])
    ctr.set_up([0.0, -1.0, 0.0])
    ctr.set_zoom(0.6)
    
    vis.poll_events()
    vis.update_renderer()
    
    img = np.asarray(vis.capture_screen_float_buffer(False))
    img = (img * 255).astype(np.uint8)
    Image.fromarray(img).save(filename)
    vis.destroy_window()

render(mesh, "complete_mesh.png")

cc_indices, cc_counts, _ = mesh.cluster_connected_triangles()
cc_indices = np.asarray(cc_indices)
largest_c = np.argmax(cc_counts)

# Open3D select_by_index doesn't work for faces natively in python, let's remove faces
mesh.remove_triangles_by_mask(cc_indices != largest_c)
mesh.remove_unreferenced_vertices()

render(mesh, "largest_component.png")
print("Screenshots saved.")
