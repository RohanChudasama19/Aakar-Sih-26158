import sys
import subprocess

try:
    from rosbags.rosbag1 import Reader
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rosbags"])
    from rosbags.rosbag1 import Reader

from rosbags.rosbag1 import Reader

bag_path = "data_external/mars_lvig/raw/HKairport01/HKairport01.bag"
with Reader(bag_path) as reader:
    print(f"duration: {reader.duration}")
    print(f"start: {reader.start_time}")
    print(f"end: {reader.end_time}")
    print(f"messages: {reader.message_count}")
    print("Topics:")
    for conn in reader.connections:
        print(f"  - {conn.topic} ({conn.msgtype})")
