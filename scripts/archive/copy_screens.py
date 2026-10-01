import shutil
from pathlib import Path

demo_dir = Path("demo/degraded_fast_quality")
shutil.copy2("complete_mesh.png", demo_dir / "complete_mesh.png")
shutil.copy2("largest_component.png", demo_dir / "largest_component.png")
