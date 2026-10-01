import os
import shutil
from pathlib import Path
import trimesh
import json

def get_size(start_path):
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
    except:
        pass
    return total_size

print("=== DISK VOLUMES ===")
for drive in ['C:\\', 'D:\\', 'E:\\']:
    if os.path.exists(drive):
        total, used, free = shutil.disk_usage(drive)
        print(f"{drive}: {free / (1024**3):.2f} GB free of {total / (1024**3):.2f} GB")

print("\n=== DIRECTORY SIZES ===")
data_dir = Path("data")
if data_dir.exists():
    for d in data_dir.iterdir():
        if d.is_dir():
            size_mb = get_size(d) / (1024**2)
            print(f"data/{d.name}: {size_mb:.2f} MB")
            
demo_dir = Path("demo")
if demo_dir.exists():
    for d in demo_dir.iterdir():
        if d.is_dir():
            size_mb = get_size(d) / (1024**2)
            print(f"demo/{d.name}: {size_mb:.2f} MB")

print("\n=== SAMPLE JOB ARTIFACTS ===")
sample_job_id = "e1403ebf-70df-47ec-8f01-5e1285c66cb9"
sample_dir = data_dir / sample_job_id
if sample_dir.exists():
    out = sample_dir / "work" / "outputs"
    print(f"Directory exists: {out.exists()}")
    
    ply_path = out / "dense_relative.ply"
    if ply_path.exists():
        pc_size = os.path.getsize(ply_path) / (1024**2)
        print(f"Dense cloud: YES ({pc_size:.2f} MB)")
    else:
        print("Dense cloud: NO")
        
    glb_path = out / "model.glb"
    if glb_path.exists():
        glb_size = os.path.getsize(glb_path) / (1024**2)
        print(f"GLB: YES ({glb_size:.2f} MB)")
        try:
            mesh = trimesh.load(str(glb_path), force='mesh')
            print(f"Mesh stats: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
        except:
            print("Mesh stats: Failed to load")
    else:
        print("GLB: NO")
        
    tex_path = out / "texture_atlas_final.png"
    if tex_path.exists():
        tex_size = os.path.getsize(tex_path) / (1024**2)
        print(f"Texture: YES ({tex_size:.2f} MB)")
    else:
        print("Texture: NO")
        
    report_path = out / "mission_report.json"
    if report_path.exists():
        with open(report_path) as f:
            r = json.load(f)
            print(f"Quality report: YES, metric_state={r.get('metric_state')}")
    else:
        print("Quality report: NO")

