import sys, json
from pathlib import Path
import numpy as np
import trimesh

sys.path.insert(0, str(Path.cwd()))
from scipy.spatial.transform import Rotation

work = Path("data/mars_hkairport01_quality/work")
dense_dir = work / "dense_mars"

# Check what percentage of faces actually got mapped to valid UV
glb = trimesh.load(str(dense_dir / "mesh_textured.glb"), process=False, force='mesh')
print(f"GLB vertices: {len(glb.vertices)}, faces: {len(glb.faces)}")

# If UV available, what fraction is in [0,1] range?
if hasattr(glb.visual, 'uv') and glb.visual.uv is not None:
    uv = glb.visual.uv
    valid = np.all((uv >= 0.01) & (uv <= 0.99), axis=1)
    print(f"UVs total: {len(uv)}, in-bounds: {valid.sum()} ({valid.mean()*100:.1f}%)")
elif hasattr(glb.visual, 'kind'):
    print(f"Visual kind: {glb.visual.kind}")

# The problem: texture_mesh passes raw COLMAP mesh vertices to project into images.
# But in COLMAP frame, cameras are BELOW the mesh (camera Z mean=0.1 vs mesh Z mean=2.8).
# So when we project mesh->camera, the camera SEES the UNDERSIDE -- all faces project
# to negative Z (behind camera), resulting in gray/untextured output.
# 
# The mesh we need to texture is mesh_raw.ply -- but we need to use the Rx180-corrected
# camera poses to project correctly.

# Load mesh_raw (in original COLMAP frame)
mesh_raw = trimesh.load(str(dense_dir / "mesh_raw.ply"), process=False)
verts = np.asarray(mesh_raw.vertices)

# Load a sample camera pose and check projection
lines = (dense_dir / "sparse_txt" / "images.txt").read_text().splitlines()
i = 0
while i < len(lines):
    l = lines[i].strip(); i += 1
    if not l or l.startswith('#'): continue
    vals = l.split()
    qw,qx,qy,qz = map(float, vals[1:5])
    tx,ty,tz = map(float, vals[5:8])
    name = vals[9]
    R = Rotation.from_quat([qx,qy,qz,qw]).as_matrix()
    t = np.array([tx,ty,tz])
    # Project mesh vertices through this camera
    cam_coords = verts @ R.T + t
    in_front = (cam_coords[:,2] > 0).sum()
    print(f"Camera {name}: {in_front}/{len(verts)} vertices in front ({in_front/len(verts)*100:.1f}%)")
    i += 1
    if i > 20: break
