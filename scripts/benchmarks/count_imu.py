from pathlib import Path
from rosbags.highlevel import AnyReader
with AnyReader([Path("data_external/mars_lvig/raw/HKairport01/HKairport01.bag")]) as reader:
    counts = {}
    for c in reader.connections:
        counts[c.topic] = counts.get(c.topic, 0) + c.msgcount
    print(f"IMU: {counts.get('/dji_osdk_ros/imu', 0)}")
