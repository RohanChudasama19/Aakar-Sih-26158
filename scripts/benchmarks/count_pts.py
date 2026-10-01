import trimesh
from pathlib import Path

dense_dir = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon\data\b3198000-1dd2-4a74-95ee-937f56510279\work\dense_balanced")
for v in ["CURRENT", "MODERATE_FUSION", "RELAXED_FUSION"]:
    f = dense_dir / f"fused_{v}.ply"
    if f.exists():
        pc = trimesh.load(str(f))
        print(f"{v}: {len(pc.vertices)} points")
