import sys, json, time, shutil
from pathlib import Path
import numpy as np
import trimesh

sys.path.insert(0, str(Path.cwd()))
from app.pipeline.mesh import build_mesh
from app.pipeline.georef import transform

work = Path("data/mars_hkairport01_quality/work")
dense_dir = work / "dense_mars"
fused_ply = dense_dir / "fused.ply"

dense_pc = trimesh.load(str(fused_ply))
pts = np.asarray(dense_pc.vertices)
colors = np.asarray(dense_pc.colors)
if colors.shape[1] == 4:
    colors = colors[:, :3]

from scipy.spatial.transform import Rotation
dense_txt = dense_dir / "sparse_txt"
images_txt = dense_txt / "images.txt"
lines = images_txt.read_text().splitlines()
poses = {}
i = 0
while i < len(lines):
    l = lines[i].strip(); i += 1
    if not l or l.startswith('#'): continue
    vals = l.split()
    img_id = int(vals[0])
    qw,qx,qy,qz = map(float, vals[1:5])
    tx,ty,tz = map(float, vals[5:8])
    camera_id = int(vals[8])
    name = vals[9]
    R = Rotation.from_quat([qx,qy,qz,qw]).as_matrix()
    t = np.array([tx,ty,tz])
    pose_matrix = np.eye(4)
    pose_matrix[:3, :3] = R
    pose_matrix[:3, 3] = t
    poses[name] = pose_matrix  # Keep as numpy array!
    i += 1

cams_txt = dense_txt / "cameras.txt"
clines = cams_txt.read_text().splitlines()
for l in clines:
    if l.startswith('#'): continue
    vals = l.split()
    if vals[1] == "PINHOLE":
        fx, fy, cx, cy = map(float, vals[4:8])
        K = [[fx, 0, cx], [0, fy, cy], [0, 0, 1]]
        break

sfm = {"poses": poses}

fix_mat = np.eye(4)
fix_mat[1, 1] = -1.0
fix_mat[2, 2] = -1.0

geo = {
    "crs": "LOCAL",
    "offset": [0,0,0],
    "matrix": fix_mat.tolist(),
    "metric_state": "RELATIVE"
}

opts = {
    "profile": "QUALITY",
    "poisson_depth": 9,
    "poisson_scale": 1.05,
    "occlusion_test": True,
    "compute_support": True,
    "max_points": 10000000,
    "simplify": False
}

print("Running full build_mesh (Poisson + Texture)...")
try:
    report = build_mesh(
        points=pts,
        colors=colors,
        geo=geo,
        sfm=sfm,
        k=K,
        directory=work,
        out_dir=dense_dir,
        options=opts
    )
    (dense_dir / "mesh_pipeline_report.json").write_text(json.dumps(report, indent=2))
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
