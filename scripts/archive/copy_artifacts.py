from pathlib import Path
import shutil

src = Path("demo/mars_hkairport01_quality")
dst = Path("data/mars_hkairport01_quality/work/outputs")
dst.mkdir(parents=True, exist_ok=True)

# mesh.glb -> model.glb
if (src / "mesh.glb").exists():
    shutil.copy2(src / "mesh.glb", dst / "model.glb")
    print("Copied model.glb")

# dense_cloud.ply -> cloud_relative.ply
if (src / "dense_cloud.ply").exists():
    shutil.copy2(src / "dense_cloud.ply", dst / "cloud_relative.ply")
    print("Copied cloud_relative.ply")
