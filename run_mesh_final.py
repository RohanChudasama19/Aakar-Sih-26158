import sys, time, json
from pathlib import Path
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation
import open3d as o3d
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path.cwd()))

work = Path("data/mars_hkairport01_quality/work")
dense_dir = work / "dense_mars"
fused_ply = dense_dir / "fused.ply"

# Load dense cloud
dense_pc = trimesh.load(str(fused_ply))
pts = np.asarray(dense_pc.vertices)
colors = np.asarray(dense_pc.colors)[:, :3]
print(f"Loaded {len(pts):,} dense points")

# Load cameras from dense sparse model (already in correct frame relative to fused.ply)
from app.pipeline.colmap import resolve_colmap_executable, get_colmap_env
import subprocess

colmap_exe = resolve_colmap_executable()
env = get_colmap_env()
dense_txt = dense_dir / "sparse_txt"

images_txt = dense_txt / "images.txt"
lines = images_txt.read_text().splitlines()
cameras = []
i = 0
while i < len(lines):
    l = lines[i].strip(); i += 1
    if not l or l.startswith('#'): continue
    vals = l.split()
    qw,qx,qy,qz = map(float, vals[1:5])
    tx,ty,tz = map(float, vals[5:8])
    R = Rotation.from_quat([qx,qy,qz,qw]).as_matrix()
    C = -R.T @ np.array([tx,ty,tz])
    cameras.append(C)
    i += 1
cameras = np.array(cameras)
print(f"Cameras: {len(cameras)}")

cloud_z_mean = pts[:,2].mean()
cam_z_mean = cameras[:,2].mean()
print(f"Cloud Z mean: {cloud_z_mean:.3f}, Camera Z mean: {cam_z_mean:.3f}")

# Since cameras are below cloud (COLMAP nadir convention), flip Z for both
# so cameras appear above the terrain for correct normal orientation
if cam_z_mean < cloud_z_mean:
    print("Applying Z-flip to align camera frame")
    pts_aligned = pts.copy(); pts_aligned[:,2] = -pts[:,2]
    cameras_aligned = cameras.copy(); cameras_aligned[:,2] = -cameras[:,2]
else:
    pts_aligned = pts
    cameras_aligned = cameras

from app.pipeline.surface import reconstruct_surface

opts = {
    "profile": "QUALITY",
    "poisson_depth": 9,
    "poisson_scale": 1.05
}

t1 = time.monotonic()
mesh, result = reconstruct_surface(
    pts_aligned, colors, cameras_aligned, max_points=10000000, options=opts
)
t_mesh = time.monotonic() - t1
print(f"Meshing runtime: {t_mesh:.1f}s")
print(f"Vertices: {len(mesh.vertices):,}")
print(f"Faces: {len(mesh.faces):,}")

# Flip Z back on the mesh
verts = np.array(mesh.vertices)
verts[:,2] = -verts[:,2]
mesh_final = trimesh.Trimesh(vertices=verts, faces=mesh.faces, vertex_colors=mesh.visual.vertex_colors, process=False)

# Connected components
import scipy.sparse as sp
import scipy.sparse.csgraph as csg
edges = mesh_final.edges_unique
adj = sp.coo_matrix((np.ones(len(edges)), (edges[:,0], edges[:,1])), shape=(len(verts), len(verts)))
adj = adj + adj.T
n, labels = csg.connected_components(adj, directed=False)
print(f"Connected components: {n}")
face_labels = labels[mesh_final.faces[:,0]]
sizes = np.bincount(labels)
largest_v = sizes.argmax()
largest_fraction = float((face_labels == largest_v).sum() / len(mesh_final.faces))
print(f"Largest component: {largest_fraction*100:.1f}%")

weak_faces = result.get('weak_face_ratio', 0)
print(f"Weak faces: {weak_faces*100:.2f}%")

out_mesh = dense_dir / "mesh_final.ply"
mesh_final.export(str(out_mesh))
print(f"Mesh saved: {out_mesh}")

# Gate check
lc_ok = largest_fraction >= 0.90
wf_ok = weak_faces <= 0.15
print(f"\n=== PHASE 7 ACCEPTANCE GATE ===")
print(f"Largest component >= 90%: {largest_fraction*100:.1f}% -> {'PASS' if lc_ok else 'FAIL'}")
print(f"Weak faces <= 15%: {weak_faces*100:.2f}% -> {'PASS' if wf_ok else 'FAIL'}")
print(f"OVERALL: {'PASS' if lc_ok and wf_ok else 'FAIL'}")

report = {
    "dense_points": len(pts),
    "vertices": len(mesh_final.vertices),
    "faces": len(mesh_final.faces),
    "connected_components": int(n),
    "largest_component_fraction": round(largest_fraction, 4),
    "weak_face_ratio": round(weak_faces, 4),
    "meshing_runtime_s": round(t_mesh, 1),
    "gate_largest_component": "PASS" if lc_ok else "FAIL",
    "gate_weak_faces": "PASS" if wf_ok else "FAIL",
    "overall_gate": "PASS" if lc_ok and wf_ok else "FAIL"
}
(dense_dir / "mesh_report.json").write_text(json.dumps(report, indent=2))
print("mesh_report.json saved")
