import json
from pathlib import Path

# Check mars_lvig mission metadata
mars = Path("data_external/mars_lvig")

for f in sorted(mars.rglob("*.json")):
    try:
        d = json.loads(f.read_text())
        print(f"FILE: {f}")
        print(json.dumps(d, indent=2)[:800])
        print("---")
    except:
        pass
