import json
from pathlib import Path
work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
poses = json.loads((work_dir / "poses.json").read_text())
print(list(poses.keys())[:5])
