import cv2
from pathlib import Path

out_dir = Path("demo/live_mars_input")
out_dir.mkdir(parents=True, exist_ok=True)

originals_dir = Path("data/mars_hkairport01_quality/work/originals")
frames = sorted(list(originals_dir.glob("*.jpg")))

print(f"Auth frames found: {len(frames)}")

if not frames:
    print("No frames found")
    exit(1)

# Read first frame to get dimensions
first = cv2.imread(str(frames[0]))
h, w = first.shape[:2]

out_video = out_dir / "derived_mars_video.mp4"
if out_video.exists():
    out_video.unlink()

# Use mp4v which is widely supported by OpenCV
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(str(out_video), fourcc, 10.0, (w, h))

for f in frames:
    img = cv2.imread(str(f))
    out.write(img)

out.release()
print(f"Video generated at {out_video} with {len(frames)} frames at {w}x{h}")
