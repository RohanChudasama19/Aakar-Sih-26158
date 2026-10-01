from rosbags.rosbag1 import Reader

bag_path = "data_external/mars_lvig/raw/HKairport01/HKairport01.bag"
with Reader(bag_path) as reader:
    counts = {}
    for conn in reader.connections:
        counts[conn.topic] = conn.msgcount
        
    for topic, count in counts.items():
        if topic in ["/left_camera/image/compressed", "/dji_osdk_ros/gps_position", "/dji_osdk_ros/rtk_position", "/livox/lidar"]:
            print(f"{topic}: {count} msgs, rate: {count / (reader.duration / 1e9):.2f} Hz")
            
    # get a sample camera image to find resolution
    for conn, timestamp, rawdata in reader.messages():
        if conn.topic == "/left_camera/image/compressed":
            from rosbags.serde import deserialize_ros1
            msg = deserialize_ros1(rawdata, conn.msgtype)
            print(f"Format: {msg.format}")
            break
