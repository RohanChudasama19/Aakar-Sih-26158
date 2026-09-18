# MARS-LVIG Adapter Notes

## Container Type
- Assumed **ROS 1 Bag** based on typical HKU MARS Lab datasets (e.g., FAST-LIO datasets).

## Topic List (Discovered / Expected)
When running the adapter on a real bag, it should look for the following topics (or equivalents depending on specific sequence):
- **/camera/image_color** or **/camera/image_raw** (RGB Image)
- **/camera/camera_info** (Camera Calibration)
- **/imu/data** or **/mavros/imu/data** (IMU)
- **/gnss/data** or **/ublox/fix** (GNSS)
- **/livox/lidar** (LiDAR)
- **/rtk/odom** or **/ground_truth/pose** (RTK / Ground Truth Trajectory)

*Note: Extract RGB frames preserving original sequence order, exact source timestamp, original dimensions, and encoding. Original sensor/image timestamps are authoritative. If images are converted to MP4, do not replace original timestamps with MP4 frame timing. Generate rame_timestamps.csv.*
