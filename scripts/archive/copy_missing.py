import shutil
from pathlib import Path

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work/dense_10_source_full")
demo_dir = Path("demo/degraded_fast_quality")

shutil.copy2(work_dir / "largest_component_textured.glb", demo_dir / "largest_component_textured.glb")
shutil.copy2(work_dir / "largest_component_textured.ply", demo_dir / "largest_component.ply")
