import numpy as np
import open3d as o3d
import trimesh

# Create a simple mesh
mesh = trimesh.creation.box()
vertices = np.asarray(mesh.vertices, dtype=np.float32)
faces = np.asarray(mesh.faces, dtype=np.uint32)

print("Setting up O3D raycasting scene...")
o3d_mesh = o3d.t.geometry.TriangleMesh()
o3d_mesh.vertex.positions = o3d.core.Tensor(vertices)
o3d_mesh.triangle.indices = o3d.core.Tensor(faces)

scene = o3d.t.geometry.RaycastingScene()
scene.add_triangles(o3d_mesh)

rays = np.array([[0, 0, 5, 0, 0, -1], [5, 5, 5, 0, 0, -1]], dtype=np.float32)
rays_tensor = o3d.core.Tensor(rays)

ans = scene.cast_rays(rays_tensor)
print(ans["geometry_ids"].numpy())
print(ans["primitive_ids"].numpy())
