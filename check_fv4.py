from pathlib import Path
import json, os, hashlib

# Check FAST_VALIDATION sparse model
fv = Path("data/FAST_VALIDATION")

# Check sparse
sparse_dirs = list((fv / "work").glob("sparse*"))
for sd in sparse_dirs:
    print(f"Sparse dir: {sd}")
    for f in sorted(sd.rglob("*")):
        sz = f.stat().st_size if f.is_file() else ""
        print(f"  {f.relative_to(sd)} {sz}")

# Check outputs
out = fv / "work" / "outputs"
for f in sorted(out.rglob("*")):
    sz = f.stat().st_size if f.is_file() else ""
    print(f"OUTPUT: {f.name} {sz}")
    if f.suffix == ".json":
        print(json.dumps(json.loads(f.read_text()), indent=2)[:500])
