import time
import subprocess
from pathlib import Path
import json
import numpy as np
import cv2
import csv
import trimesh
from scipy.spatial.transform import Rotation
from app.camera import CameraModelType, CameraModel
from app.schemas import telemetry
from app.pipeline.georef import align
from app.pipeline.mesh import build_mesh
from app.pipeline.texture import texture_mesh

def run_meshing():
    t_start = time.time()
    input_dir = Path("workspace/HKairport01_FAST_C_FINAL/inputs")
    work = Path("workspace/HKairport01_FAST_C_FINAL/work")
    dense_dir = work / "dense_fast"
    
    gps = telemetry(input_dir / "gps.csv")
    frames_dir = input_dir / "images"
    info = {"frames": [{"name": p.name} for p in sorted(frames_dir.glob("*.jpg"))]}
    
    with open("data_external/mars_lvig/processed/HKairport01/FAST/frames.csv") as f:
        times = {r["filename"]: float(r["timestamp"]) for r in csv.DictReader(f)}
    for fr in info["frames"]:
        fr["time_sec"] = times[fr["name"]]
    info["start_time_utc"] = 0.0
    
    scale_factor = 1024 / 2448.0
    w = int(2448 * scale_factor)
    h = int(2048 * scale_factor)
    cam = CameraModel(CameraModelType.PINHOLE, w, h, 600, 600, w//2, h//2)
    
    textdir = input_dir / "sparse_txt"
    poses = {}
    lines = (textdir / "images.txt").read_text().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line or line.startswith("#"): continue
        values = line.split()
        qw, qx, qy, qz = map(float, values[1:5])
        rot = Rotation.from_quat([qx, qy, qz, qw]).as_matrix()
        cname = values[9]
        idx = next((n for n, f in enumerate(info["frames"]) if f["name"] == cname), None)
        if idx is not None:
            poses[idx] = np.c_[rot, np.array(values[5:8], float)]
        i += 1
        
    points_3d = []
    with open(textdir / "points3D.txt") as f:
        for line in f:
            if line.startswith("#"): continue
            points_3d.append(line.split()[1:4])
            
    sfm = {
        "poses": poses,
        "model_path": str(input_dir / "sparse" / "0"),
        "points": np.array(points_3d, float)
    }
    
    geo = align(sfm, info, gps, input_dir)
    
    opts = {
        "profile": "FAST",
        "force_profile": "FAST",
        "mesh_decimation": 50000,
        "texture_resolution": 2048,
        "max_image_size": 1024
    }
    
    print("Loading points...")
    ply = trimesh.load(work / "dense_fast" / "fused.ply")
    points = np.array(ply.vertices)
    colors = np.array(ply.visual.vertex_colors[:, :3])
    print(f"Points loaded: {len(points)}")
    
    print("Mapping undistorted images for texture.py...")
    dense_images = dense_dir / "images"
    for idx, fr in enumerate(info["frames"]):
        orig_name = fr["name"]
        undist_path = dense_images / orig_name
        target_path = dense_images / f"{idx:06d}.png"
        if undist_path.exists():
            img = cv2.imread(str(undist_path))
            if img is not None:
                cv2.imwrite(str(target_path), img)
                
    print("Executing Mesh & Texture...")
    t0_mesh = time.time()
    
    from app.pipeline.surface import reconstruct_surface
    local_pts = points - np.array(geo["origin"])
    cameras = np.array([-p[:, :3].T @ p[:, 3] for p in sfm["poses"].values()])
    cameras = cameras - np.array(geo["origin"])
    
    mesh, _ = reconstruct_surface(local_pts, colors, cameras, options=opts)
    
    print(f"Mesh has {len(mesh.vertices)} vertices and {len(mesh.faces)} faces")
    
    out_mesh = texture_mesh(mesh, geo, sfm, cam.to_matrix(), dense_images, opts)
    if not out_mesh:
        out_mesh = mesh
    
    t_mesh = time.time() - t0_mesh
    
    print("Executing Export...")
    t0_export = time.time()
    glb_path = work / "model.glb"
    out_mesh.export(glb_path)
    t_export = time.time() - t0_export
    
    print(f"\nMesh/Texture: {t_mesh:.2f} s")
    print(f"Export GLB: {t_export:.2f} s")
    print(f"GLB size: {glb_path.stat().st_size / 1024**2:.2f} MB")
    print(f"Faces: {len(out_mesh.faces)}")
    print(f"Vertices: {len(out_mesh.vertices)}")
    
if __name__ == "__main__":
    run_meshing()
