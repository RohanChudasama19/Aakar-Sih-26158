from pathlib import Path
import json, os

# Check demo/degraded_fast_quality full inventory
dq = Path("demo/degraded_fast_quality")
print("=== degraded_fast_quality contents ===")
for f in sorted(dq.rglob("*")):
    if f.is_file():
        print(f"  {f.name} ({f.stat().st_size:,} bytes)")

manifest_path = dq / "manifest.json"
if manifest_path.exists():
    m = json.loads(manifest_path.read_text())
    print()
    print("=== manifest.json ===")
    print(json.dumps(m, indent=2)[:1200])
