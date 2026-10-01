import open3d as o3d, numpy as np, cv2
from pathlib import Path

glb = "data/mars_hkairport01_quality/work/dense_mars/mesh_textured.glb"
demo = Path("demo/mars_hkairport01_quality")

mesh = o3d.io.read_triangle_mesh(glb)
mesh.compute_vertex_normals()
print(f"Loaded textured GLB: {len(mesh.vertices)} verts, {len(mesh.triangles)} faces")
print(f"Has textures: {mesh.has_textures()}")
print(f"Has UVs: {mesh.has_triangle_uvs()}")
print(f"Has vertex colors: {mesh.has_vertex_colors()}")

# Screenshot textured mesh
def snap(name, front, up, zoom=0.35):
    vis = o3d.visualization.Visualizer()
    vis.create_window(visible=False, width=1920, height=1080)
    vis.add_geometry(mesh)
    vc = vis.get_view_control()
    vc.set_lookat(mesh.get_axis_aligned_bounding_box().get_center().tolist())
    vc.set_front(front)
    vc.set_up(up)
    vc.set_zoom(zoom)
    vis.poll_events()
    vis.update_renderer()
    img = np.asarray(vis.capture_screen_float_buffer(False))
    vis.destroy_window()
    out = demo / f"texture_{name}.png"
    cv2.imwrite(str(out), cv2.cvtColor((img*255).astype(np.uint8), cv2.COLOR_RGB2BGR))
    print(f"  Saved {out.name}")

snap("top_down", [0,0,1], [0,-1,0], 0.40)
snap("oblique", [-0.5,-0.7,0.5], [0,0,1], 0.40)
print("Done")
