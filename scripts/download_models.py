"""Optional trusted model setup. Check Ultralytics licence terms before deployment."""
from pathlib import Path
import shutil
from ultralytics import YOLO
out=Path(__file__).resolve().parents[1]/'weights'; out.mkdir(exist_ok=True)
model=YOLO('yolov8s-seg.pt')
source=Path(model.ckpt_path).resolve()
if source != (out/source.name).resolve(): shutil.copy(source,out/source.name)
print('Trusted segmentation model:',out/source.name)
print('Set SEGMENTATION_MODEL to this absolute path before starting the server/worker.')
