import json
from pathlib import Path

# Read flight_metadata from FAST_VALIDATION
inputs = Path("data/FAST_VALIDATION/inputs")
for f in sorted(inputs.iterdir()):
    print(f.name, f.stat().st_size if f.is_file() else "DIR")

meta = inputs / "flight_metadata.json"
if meta.exists():
    print(json.dumps(json.loads(meta.read_text()), indent=2))
