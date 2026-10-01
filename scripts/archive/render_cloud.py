import open3d as o3d
import numpy as np
import cv2
from pathlib import Path

# Load and render POINT CLOUD (not mesh) to see true density
pc = o3d.io.read_point_cloud("data/mars_hkairport01_quality/work/dense_mars/fused.ply")
print(f"Points: {len(pc.points)}")

# Top-down view
vis = o3d.visualization.Visualizer()
vis.create_window(visible=False, width=1920, height=1080)
vis.add_geometry(pc)
vc = vis.get_view_control()
vc.set_front([0, 0, -1])
vc.set_lookat([0.5, 0, 3])
vc.set_up([0, -1, 0])
vc.set_zoom(0.3)
vis.poll_events()
vis.update_renderer()
img = vis.capture_screen_float_buffer(False)
vis.destroy_window()
img_u8 = (np.asarray(img)*255).astype(np.uint8)
cv2.imwrite("data/mars_hkairport01_quality/work/dense_mars/screenshot_cloud_top.png",
            cv2.cvtColor(img_u8, cv2.COLOR_RGB2BGR))
print("Cloud top-down saved")

# Oblique view
vis2 = o3d.visualization.Visualizer()
vis2.create_window(visible=False, width=1920, height=1080)
vis2.add_geometry(pc)
vc2 = vis2.get_view_control()
vc2.set_front([0.5, -0.5, -0.7])
vc2.set_lookat([0.5, 0, 3])
vc2.set_up([0, 0, -1])
vc2.set_zoom(0.3)
vis2.poll_events()
vis2.update_renderer()
img2 = vis2.capture_screen_float_buffer(False)
vis2.destroy_window()
img_u8b = (np.asarray(img2)*255).astype(np.uint8)
cv2.imwrite("data/mars_hkairport01_quality/work/dense_mars/screenshot_cloud_oblique.png",
            cv2.cvtColor(img_u8b, cv2.COLOR_RGB2BGR))
print("Cloud oblique saved")
