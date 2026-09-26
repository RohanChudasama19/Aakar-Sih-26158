import open3d as o3d
import numpy as np
import cv2
from pathlib import Path

mesh_path = "data/mars_hkairport01_quality/work/dense_mars/mesh.ply"
mesh = o3d.io.read_triangle_mesh(mesh_path)
mesh.compute_vertex_normals()

# Fit camera to mesh
bbox = mesh.get_axis_aligned_bounding_box()
center = bbox.get_center()
extent = bbox.get_extent()
print(f"Mesh center: {center}")
print(f"Mesh extent: {extent}")

# Generate multiple view screenshots
views = [
    ("top_down", [0, 0, max(extent)*2], [0, -1, 0]),
    ("oblique_se", [extent[0], -extent[1], max(extent)*1.5], [0, 0, 1]),
    ("side_north", [0, -max(extent)*2, extent[2]], [0, 0, 1]),
]

for name, eye_offset, up in views:
    vis = o3d.visualization.Visualizer()
    vis.create_window(visible=False, width=1280, height=720)
    vis.add_geometry(mesh)
    vc = vis.get_view_control()
    vc.set_lookat(center.tolist())
    eye = (center + np.array(eye_offset)).tolist()
    vc.set_front((np.array(eye_offset) / np.linalg.norm(eye_offset)).tolist())
    vc.set_up(up)
    vc.set_zoom(0.5)
    vis.poll_events()
    vis.update_renderer()
    img = vis.capture_screen_float_buffer(False)
    vis.destroy_window()
    img_u8 = (np.asarray(img)*255).astype(np.uint8)
    out = f"data/mars_hkairport01_quality/work/dense_mars/screenshot_{name}.png"
    cv2.imwrite(out, cv2.cvtColor(img_u8, cv2.COLOR_RGB2BGR))
    print(f"Saved {out}")

print("Done")
