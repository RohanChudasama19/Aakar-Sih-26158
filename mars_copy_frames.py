import shutil, csv, json
from pathlib import Path

src = Path("data_external/mars_lvig/processed/HKairport01/FAST/images")
work = Path("data/mars_hkairport01_quality/work")
frames_out = work / "frames"
orig_out = work / "originals"

all_frames = sorted(src.glob("frame_*.jpg"))
# Select every 2nd: 200 frames
step = 2
selected = all_frames[::step][:200]
print(f"Selecting {len(selected)} of {len(all_frames)} frames")

for f in selected:
    shutil.copy2(f, frames_out / f.name)
    shutil.copy2(f, orig_out / f.name)

print(f"Copied {len(selected)} frames to frames/ and originals/")
print(f"First: {selected[0].name}, Last: {selected[-1].name}")

# Read GPS and write matching subset
gps_path = Path("data_external/mars_lvig/processed/HKairport01/FAST/gps.csv")
rows = list(csv.DictReader(open(gps_path)))
selected_indices = set(i*step for i in range(len(selected)))
selected_rows = [r for i, r in enumerate(rows) if i in selected_indices]
print(f"GPS rows selected: {len(selected_rows)}")

# Save flight metadata
meta = {
    "mission_name": "MARS-LVIG HKairport01",
    "dataset": "MARS-LVIG",
    "sequence": "HKairport01",
    "source_provenance": "ROS bag /left_camera/image/compressed",
    "original_video_available": False,
    "reconstruction_mode": "FRAME-BASED",
    "frame_count": len(selected),
    "total_frames_available": len(all_frames),
    "selection_step": step,
    "effective_fps": 0.94,
    "gps_per_frame": True,
    "gps_source": "/dji_osdk_ros/gps_position",
    "camera_intrinsics": "ESTIMATED_BY_COLMAP",
    "resolution": "1280x1070"
}
(work.parent / "inputs" / "mission_meta.json").write_text(json.dumps(meta, indent=2))
print("Wrote mission_meta.json")