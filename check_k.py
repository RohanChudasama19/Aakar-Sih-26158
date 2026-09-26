import json
from pathlib import Path
work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
pre = json.loads((work_dir / "preprocess.json").read_text())
print(pre.get("camera_matrix"))
