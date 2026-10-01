import open3d as o3d
import numpy as np
import cv2
from pathlib import Path

mesh = o3d.io.read_triangle_mesh("data/mars_hkairport01_quality/work/dense_mars/mesh_final.ply")
mesh.compute_vertex_normals()
bbox = mesh.get_axis_aligned_bounding_box()
center = bbox.get_center()
extent = bbox.get_extent()
print(f"Mesh center: {center}, extent: {extent}")

out_dir = Path("data/mars_hkairport01_quality/work/dense_mars")

def snap(name, front, up, zoom=0.35):
    vis = o3d.visualization.Visualizer()
    vis.create_window(visible=False, width=1920, height=1080)
    vis.add_geometry(mesh)
    vc = vis.get_view_control()
    vc.set_lookat(center.tolist())
    vc.set_front(front)
    vc.set_up(up)
    vc.set_zoom(zoom)
    vis.poll_events()
    vis.update_renderer()
    img = np.asarray(vis.capture_screen_float_buffer(False))
    vis.destroy_window()
    cv2.imwrite(str(out_dir / f"mesh_{name}.png"), cv2.cvtColor((img*255).astype(np.uint8), cv2.COLOR_RGB2BGR))
    print(f"  Saved mesh_{name}.png")

snap("top_down",    [0, 0, 1],        [0, -1, 0],  0.40)
snap("oblique_sw",  [-0.6, -0.8, 0.5],[0, 0, 1],   0.40)
snap("oblique_ne",  [0.6, 0.8, 0.5],  [0, 0, 1],   0.40)
snap("side_east",   [1, 0, 0.3],      [0, 0, 1],   0.40)
print("All screenshots saved")
