from pathlib import Path
work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
diag_dir = work_dir / "preserved_dense_diagnostics"
depth_map = list(diag_dir.glob("*_depth_maps.photometric.bin"))[0]
with open(depth_map, "rb") as f:
    print(f.read(50))
