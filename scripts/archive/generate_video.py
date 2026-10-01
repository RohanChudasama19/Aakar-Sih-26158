import subprocess
from pathlib import Path

out_dir = Path("demo/live_mars_input")
out_dir.mkdir(parents=True, exist_ok=True)

# Create a text file for ffmpeg concat demuxer
originals_dir = Path("data/mars_hkairport01_quality/work/originals")
frames = sorted(list(originals_dir.glob("*.jpg")))

list_path = out_dir / "frames.txt"
with open(list_path, "w") as f:
    for frame in frames:
        f.write(f"file '{frame.resolve().as_posix()}'\n")
        f.write(f"duration 0.1\n") # 10 FPS => 0.1s per frame

# Duplicate the last frame to avoid ffmpeg bug
with open(list_path, "a") as f:
    f.write(f"file '{frames[-1].resolve().as_posix()}'\n")

print(f"Auth frames found: {len(frames)}")

# Run ffmpeg to encode visually lossless x264 (crf 15)
out_video = out_dir / "derived_mars_video.mp4"
if out_video.exists():
    out_video.unlink()

cmd = [
    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_path),
    "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-pix_fmt", "yuv420p",
    str(out_video)
]

try:
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    print(f"Video generated at {out_video}")
except subprocess.CalledProcessError as e:
    print(f"FFmpeg failed: {e.stderr}")
