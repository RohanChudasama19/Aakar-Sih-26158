import hashlib
from pathlib import Path

demo_dir = Path("demo/degraded_fast_quality")
if not demo_dir.exists():
    print("Demo directory missing!")
else:
    for p in demo_dir.glob("*.*"):
        if p.is_file():
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            print(f"{p.name}: {h}")
