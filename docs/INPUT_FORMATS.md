# Input contracts

Use `samples/` as the exact worked example. Frame indices are zero-based decoded video frame indices. GPS timestamps must be UTC, strictly increasing and consistent with video time. This build uses frame indices for association; it does not estimate clock offsets. A constant-FPS video is expected; variable-FPS video should first be converted and telemetry resampled to that timeline.

## Required GPS CSV

```
timestamp_utc,frame,latitude,longitude,altitude_m,compass_heading_deg,gimbal_pitch_deg,gimbal_yaw_deg,speed_mps,satellites
2026-01-01T00:00:00Z,0,22.94,72.36,63,90,-60,0,1.7,18
```

Provide at least three monotonically ordered samples covering selected video frames. Coordinates are WGS84 latitude/longitude in degrees. Altitude must have a consistent declared datum across GPS, barometer and corrections. Interpolation uses frame number; no telemetry extrapolation. Heading/gimbal/speed/satellite fields are validated and retained, but they do not independently establish metric accuracy or camera attitude in this build.

## Required flight JSON

See `samples/flight.json`. Required fields exactly match the supplied build prompt: `mission_name`, `drone_model`, `camera_sensor`, `video_file`, `video_resolution`, `video_fps`, `video_duration_sec`, `home_point`, `start_time_utc`, `end_time_utc`, `camera_intrinsics`.

Intrinsics use focal length and sensor dimensions in millimetres, with image width/height in pixels. Pinhole/zero-distortion images are assumed. Undistort fisheye/wide-angle video externally and supply matching intrinsics. Incorrect focal length or lens distortion biases geometry.

## Camera intrinsics override JSON

```json
{"fx":550,"fy":550,"cx":320,"cy":240,"image_width_px":640,"image_height_px":480}
```

These pixel intrinsics are scaled to the processing resolution. Alternatively use the same focal-length/sensor schema as flight metadata.

## RTK/PPK CSV

```
frame,east_correction_m,north_correction_m,up_correction_m
0,0.12,-0.04,0.07
59,0.13,-0.03,0.08
```

These are **additive local UTM corrections in metres**, not absolute RTK coordinates and not raw RINEX observations. Corrections are interpolated before robust similarity alignment. The UI/report records whether applied. Raw PPK solving is outside this build. Corrections must cover the complete GPS frame range; extrapolation is rejected.

## Barometer CSV

```
frame,altitude_m
0,63.0
59,63.0
```

Absolute altitude in the same vertical datum as GPS. It replaces interpolated GPS altitude before alignment. Relative barometer readings must first be anchored to a known altitude.

## IMU CSV

The optional file is archived for reproducibility, but **IMU fusion is not implemented**. The form and report disclose this. A calibrated IMU-to-camera rigid transform, gravity convention, clock synchronization, noise model and bias estimator are needed to implement a trustworthy ESKF; inventing those values would degrade the result.

## Custom checkpoints

- Segmentation: a trusted Ultralytics-compatible YOLO segmentation `.pt`, using COCO class IDs for dynamic objects. Install `requirements-models.txt`. Administrator must set `ALLOW_TRUSTED_PT=1`. **PyTorch checkpoint files may execute code**; never enable uploads for untrusted users. In the standard configuration uploaded `.pt` files are rejected before loading.
- Depth: an ONNX graph with one fixed-shape float32 NCHW RGB `[0,1]` input and a positive Z-depth output `[1,1,H,W]` (or `[1,H,W]`). Fixed dimensions 32–2048. Install `requirements-models.txt`. Median scale is fit against projected sparse SfM depth; views with >25% median relative disagreement are rejected. Inferred samples are saved separately in `inferred_depth_regions.npz`, not incorporated into measured geometry. Inverse-depth/relative-disparity models require an explicit conversion/export wrapper.
- Custom pose checkpoints are **not supported**. SfM determines camera poses from calibrated multiview feature observations. This is an explicit deviation from the aspirational checkpoint-swapping requirement.
- Default model weights are not bundled. `scripts/download_models.py` downloads the official small YOLOv8 segmentation checkpoint when run in a networked environment after optional dependencies are installed. Review its AGPL/commercial licence before redistribution or service deployment.
