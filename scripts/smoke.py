import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.pipeline.runner import run_pipeline
from scripts.generate_sample import generate

root = Path(__file__).resolve().parents[1]
if not (root / "samples" / "sample.mp4").exists():
    generate(root / "samples")
inputs = root / "data" / "cli-smoke" / "inputs"
inputs.mkdir(parents=True, exist_ok=True)
for source, target in [("sample.mp4", "video.mp4"), ("gps.csv", "gps.csv"), ("flight.json", "flight.json")]:
    shutil.copy(root / "samples" / source, inputs / target)
report = run_pipeline(
    inputs,
    inputs.parent / "work",
    {"max_width": 640, "max_frames": 60},
    lambda s, p, m: print(f"{s} {p:5.1f}% {m}", flush=True),
)
assert set(report["stages"]) == set("ABCDEF")
for filename in ["model.glb", "model.obj", "cloud.ply", "report.json", "semantic_labels.npz"]:
    assert (inputs.parent / "work" / "outputs" / filename).stat().st_size > 0
print("PASS — inspect", inputs.parent / "work" / "artifacts.zip")
