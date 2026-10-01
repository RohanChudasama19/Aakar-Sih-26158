import cv2
import hashlib
from pathlib import Path

video_path = Path("demo/live_mars_input/derived_mars_video.mp4")

with open(video_path, "rb") as f:
    sha = hashlib.sha256(f.read()).hexdigest()

cap = cv2.VideoCapture(str(video_path))
frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
dur = frames / fps if fps > 0 else 0

print(f"Decoded Frames: {frames}")
print(f"Resolution: {w}x{h}")
print(f"FPS: {fps}")
print(f"Duration: {dur:.2f}s")
print(f"SHA256: {sha}")

# Test decode first frame
ret, frame = cap.read()
if ret:
    print(f"Frame 0 decoded correctly, shape: {frame.shape}")
else:
    print("FAILED to decode first frame")

cap.release()
