from pathlib import Path
from rosbags.highlevel import AnyReader
with AnyReader([Path("data_external/mars_lvig/raw/HKairport01/HKairport01.bag")]) as reader:
    for conn, timestamp, rawdata in reader.messages():
        if conn.topic == "/left_camera/image/compressed":
            msg = reader.deserialize(rawdata, conn.msgtype)
            print(f"Format: {msg.format}")
            print(f"Data size: {len(msg.data)}")
            
            with open("workspace/tmp_extract_frame.jpg", "wb") as f:
                f.write(msg.data)
            break
