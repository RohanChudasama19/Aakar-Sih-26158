from pathlib import Path, PurePosixPath
import json, os

fv = Path("data/FAST_VALIDATION")
print("FAST_VALIDATION contents:")
for f in sorted(fv.rglob("*")):
    try:
        sz = os.path.getsize(f) if f.is_file() else None
    except:
        sz = None
    print(f"  {f.relative_to(fv)} {'(' + str(sz) + 'B)' if sz else ''}")
