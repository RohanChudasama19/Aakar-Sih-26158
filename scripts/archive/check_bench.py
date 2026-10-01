from pathlib import Path
import subprocess, sys

# Check existing processed artifacts from test_benchmark
bench = Path("data/test_benchmark/work")

# Check sparse model
sparse0 = bench / "sparse" / "0"
print("sparse/0 exists:", sparse0.exists())
if sparse0.exists():
    print("  files:", [f.name for f in sparse0.iterdir()])

# Check frames
frames = bench / "originals"
if frames.exists():
    fl = sorted(frames.iterdir())
    print(f"Benchmark frames: {len(fl)}, first={fl[0].name}, last={fl[-1].name}")

# Check FAST_VALIDATION output
fv = Path("data/FAST_VALIDATION")
for f in sorted(fv.rglob("*.ply")):
    import os
    print(f"PLY: {f} size={os.path.getsize(f)}")
for f in sorted(fv.rglob("*.glb")):
    import os
    print(f"GLB: {f} size={os.path.getsize(f)}")
for f in sorted(fv.rglob("output.json")):
    import json
    print(f"OUTPUT: {f}")
    d = json.loads(f.read_text())
    print(json.dumps(d, indent=2)[:600])
