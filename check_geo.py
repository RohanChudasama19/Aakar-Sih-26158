import json
from pathlib import Path
work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
geo = json.loads((work_dir / "alignment.json").read_text())
print(json.dumps(geo, indent=2))
