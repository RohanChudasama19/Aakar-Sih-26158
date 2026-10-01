import json
import csv
from pathlib import Path

path = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon\data_external\uavscenes\raw\HKairport01\metadata\sampleinfos_interpolated.json")
with open(path) as f:
    uav = json.load(f)
uav_times = [float(d["OriginalImageName"].replace(".jpg", "")) for d in uav]

bag_path = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon\workspace\HKairport01_FAST_C_FINAL\inputs\images")
bag_images = [f.name for f in bag_path.glob("*.jpg")]
bag_times = []

with open(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon\data_external\mars_lvig\processed\HKairport01\FAST\frames.csv") as f:
    reader = csv.DictReader(f)
    frame_times = {r["filename"]: float(r["timestamp"]) for r in reader}

for name in bag_images:
    if name in frame_times:
        bag_times.append(frame_times[name] + 1671606430.0137024) # Approximate if needed, wait, let's use the actual FAST timestamps from the bag extraction

# Bag actually extracts frames with timestamp as filename if we look at the raw extraction, but HKairport01 FAST uses something else.
# Let's just read the original bag image timestamps from the ROS bag or use the ones from frames.csv
bag_times_raw = list(frame_times.values())
start_time_utc = 1671606430.0137024 # from gps.csv

print(f"UAVScenes start: {min(uav_times):.3f}, end: {max(uav_times):.3f}, count: {len(uav_times)}")
print(f"Bag start: {start_time_utc + min(bag_times_raw):.3f}, end: {start_time_utc + max(bag_times_raw):.3f}, count: {len(bag_times_raw)}")

# Check RTK csv
rtk_path = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon\data_external\uavscenes\raw\HKairport01\metadata\rtk_positions_raw.csv")
if rtk_path.exists():
    with open(rtk_path) as f:
        reader = csv.reader(f)
        header = next(reader)
        print(f"\nRTK CSV Header: {header}")
        rows = list(reader)
        print(f"RTK CSV rows: {len(rows)}")
        print(f"RTK CSV first: {rows[0]}")
