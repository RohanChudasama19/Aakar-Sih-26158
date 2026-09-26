import sys, time, json
from pathlib import Path
import numpy as np
import trimesh

sys.path.insert(0, str(Path.cwd()))
from app.pipeline.surface import reconstruct_surface

work = Path("data/mars_hkairport01_quality/work")
dense_dir = work / "dense_mars"
fused_ply = dense_dir / "fused.ply"

dense_pc = trimesh.load(str(fused_ply))
pts = np.asarray(dense_pc.vertices)
colors = np.asarray(dense_pc.colors)[:, :3]
poses_json = work / "poses.json"
poses = json.loads(poses_json.read_text())
cameras = []
for p in poses.values():
    m = np.array(p)
    R = m[:, :3]
    t = m[:, 3]
    C = -R.T @ t
    cameras.append(C)
cameras = np.array(cameras)

opts = {
    "profile": "QUALITY",
    "poisson_depth": 9,
    "poisson_scale": 1.05
}

t1 = time.monotonic()
mesh, result = reconstruct_surface(
    pts, colors, cameras, max_points=10000000, options=opts
)
print(f"Meshing runtime: {time.monotonic()-t1:.1f}s")
print(f"Vertices: {len(mesh.vertices):,}")
print(f"Faces: {len(mesh.faces):,}")

# Connected components using scipy
import scipy.sparse as sp
import scipy.sparse.csgraph as csg
edges = mesh.edges_unique
adj = sp.coo_matrix((np.ones(len(edges)), (edges[:,0], edges[:,1])), shape=(len(mesh.vertices), len(mesh.vertices)))
adj = adj + adj.T
n, labels = csg.connected_components(adj, directed=False)
print(f"Connected components: {n}")
largest_fraction = 0.0
if n > 0:
    sizes = np.bincount(labels)
    largest_v = sizes.argmax()
    face_in_largest = labels[mesh.faces[:, 0]] == largest_v
    largest_fraction = float(face_in_largest.sum() / len(mesh.faces))

print(f"Largest component: {largest_fraction*100:.1f}%")

weak_faces = result.get('weak_face_ratio', 0)
supported = result.get('supported_ratio', 0)
print(f"Weak faces: {weak_faces*100:.2f}%")
print(f"Supported faces: {supported*100:.2f}%")

out_mesh = dense_dir / "mesh.ply"
mesh.export(str(out_mesh))

report = {
    "dense_points": len(pts),
    "vertices": len(mesh.vertices),
    "faces": len(mesh.faces),
    "connected_components": int(n),
    "largest_component_fraction": round(largest_fraction, 4),
    "weak_face_ratio": round(weak_faces, 4),
    "supported_ratio": round(supported, 4),
    "meshing_runtime_s": round(time.monotonic()-t1, 1)
}
(dense_dir / "mesh_report.json").write_text(json.dumps(report, indent=2))
