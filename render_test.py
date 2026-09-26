import open3d as o3d
import numpy as np
import cv2
from pathlib import Path

mesh = o3d.io.read_triangle_mesh("data/mars_hkairport01_quality/work/dense_mars/mesh.ply")
mesh.compute_vertex_normals()

vis = o3d.visualization.Visualizer()
vis.create_window(visible=False, width=1280, height=720)
vis.add_geometry(mesh)
vis.poll_events()
vis.update_renderer()
img = vis.capture_screen_float_buffer(False)
vis.destroy_window()

img_u8 = (np.asarray(img) * 255).astype(np.uint8)
img_bgr = cv2.cvtColor(img_u8, cv2.COLOR_RGB2BGR)
cv2.imwrite("data/mars_hkairport01_quality/work/dense_mars/screenshot_mesh.png", img_bgr)
print("Screenshot saved to screenshot_mesh.png")
