# 10-Minute Video Performance Benchmark

## Dataset Limitations
A genuine 10-minute continuous UAV flight video is **NOT AVAILABLE** in the provided local storage. The longest available candidate is `colorado_dataset/video.mp4` (3.36 minutes), which also lacks matched independent reference telemetry.

Therefore, the strict official target evaluation of "< 15 minutes for a 10-minute video" is marked as **NOT_AVAILABLE**.

## Scalability Evidence
Previous processing queue logs indicate the `colorado_dataset/video.mp4` (201 seconds, 180 frames selected) processed successfully using CPU fallback in ~620-820 seconds. 

## Benchmark on Sample Video
To demonstrate the functionality of the three GPU profiles (FAST, BALANCED, QUALITY), we benchmarked them on the available `samples/sample.mp4` (6.0 seconds).
- **FAST**: 33.7s runtime, 62k dense points
- **BALANCED**: 218.9s runtime, 81k dense points
- **QUALITY**: [Pending]
