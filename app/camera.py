from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import cv2
import numpy as np


class CameraModelType(str, Enum):
    PINHOLE = "PINHOLE"
    SIMPLE_PINHOLE = "SIMPLE_PINHOLE"
    SIMPLE_RADIAL = "SIMPLE_RADIAL"
    RADIAL = "RADIAL"
    OPENCV = "OPENCV"
    OPENCV_FISHEYE = "OPENCV_FISHEYE"


class CalibrationSource(str, Enum):
    PROVIDED_CALIBRATION = "PROVIDED_CALIBRATION"
    CAMERA_DATABASE = "CAMERA_DATABASE"
    METADATA_DERIVED = "METADATA_DERIVED"
    SELF_CALIBRATED = "SELF_CALIBRATED"
    APPROXIMATED = "APPROXIMATED"


class CalibrationState(str, Enum):
    CALIBRATED = "CALIBRATED"
    PARTIALLY_CALIBRATED = "PARTIALLY_CALIBRATED"
    ESTIMATED = "ESTIMATED"
    UNKNOWN = "UNKNOWN"


@dataclass
class CameraModel:
    model_type: CameraModelType
    width: int
    height: int
    fx: float
    fy: float
    cx: float
    cy: float
    skew: float = 0.0
    distortion: List[float] = field(default_factory=list)
    source: CalibrationSource = CalibrationSource.APPROXIMATED
    state: CalibrationState = CalibrationState.UNKNOWN
    original_width: Optional[int] = None
    original_height: Optional[int] = None
    resize_scale_x: float = 1.0
    resize_scale_y: float = 1.0
    crop_offset_x: float = 0.0
    crop_offset_y: float = 0.0
    reprojection_rmse_px: Optional[float] = None

    def __post_init__(self):
        if self.original_width is None:
            self.original_width = self.width
        if self.original_height is None:
            self.original_height = self.height

    def to_matrix(self) -> np.ndarray:
        return np.array([[self.fx, self.skew, self.cx], [0.0, self.fy, self.cy], [0.0, 0.0, 1.0]], dtype=np.float64)

    def to_opencv_distortion(self) -> np.ndarray:
        """Converts internal distortion list to OpenCV-compatible numpy array."""
        dist = np.zeros(8, dtype=np.float64)
        if not self.distortion:
            return dist

        if self.model_type in (CameraModelType.PINHOLE, CameraModelType.SIMPLE_PINHOLE):
            pass
        elif self.model_type == CameraModelType.SIMPLE_RADIAL:
            dist[0] = self.distortion[0]  # k1
        elif self.model_type == CameraModelType.RADIAL:
            dist[0] = self.distortion[0]  # k1
            dist[1] = self.distortion[1]  # k2
        elif self.model_type == CameraModelType.OPENCV:
            # k1, k2, p1, p2, (optional) k3
            for i, v in enumerate(self.distortion[:5]):
                dist[i] = v
        elif self.model_type == CameraModelType.OPENCV_FISHEYE:
            for i, v in enumerate(self.distortion[:4]):
                dist[i] = v
        return dist

    def to_colmap(self) -> str:
        """Returns COLMAP parameter string."""
        if self.model_type == CameraModelType.SIMPLE_PINHOLE:
            params = [self.fx, self.cx, self.cy]
        elif self.model_type == CameraModelType.PINHOLE:
            params = [self.fx, self.fy, self.cx, self.cy]
        elif self.model_type == CameraModelType.SIMPLE_RADIAL:
            params = [self.fx, self.cx, self.cy, self.distortion[0] if self.distortion else 0.0]
        elif self.model_type == CameraModelType.RADIAL:
            params = [
                self.fx,
                self.cx,
                self.cy,
                self.distortion[0] if len(self.distortion) > 0 else 0.0,
                self.distortion[1] if len(self.distortion) > 1 else 0.0,
            ]
        elif self.model_type == CameraModelType.OPENCV:
            params = [
                self.fx,
                self.fy,
                self.cx,
                self.cy,
                self.distortion[0] if len(self.distortion) > 0 else 0.0,
                self.distortion[1] if len(self.distortion) > 1 else 0.0,
                self.distortion[2] if len(self.distortion) > 2 else 0.0,
                self.distortion[3] if len(self.distortion) > 3 else 0.0,
            ]
        else:
            # Fallback to PINHOLE
            params = [self.fx, self.fy, self.cx, self.cy]

        return ",".join(str(p) for p in params)

    def scale(self, new_width: int, new_height: int) -> "CameraModel":
        """Returns a new CameraModel scaled to the given dimensions."""
        sx = new_width / self.width
        sy = new_height / self.height
        return CameraModel(
            model_type=self.model_type,
            width=new_width,
            height=new_height,
            fx=self.fx * sx,
            fy=self.fy * sy,
            cx=self.cx * sx,
            cy=self.cy * sy,
            skew=self.skew * sx,
            distortion=self.distortion.copy(),
            source=self.source,
            state=self.state,
            original_width=self.original_width,
            original_height=self.original_height,
            resize_scale_x=self.resize_scale_x * sx,
            resize_scale_y=self.resize_scale_y * sy,
            crop_offset_x=self.crop_offset_x * sx,
            crop_offset_y=self.crop_offset_y * sy,
            reprojection_rmse_px=self.reprojection_rmse_px,
        )

    def crop(self, offset_x: float, offset_y: float, new_width: int, new_height: int) -> "CameraModel":
        """Returns a new CameraModel after cropping."""
        return CameraModel(
            model_type=self.model_type,
            width=new_width,
            height=new_height,
            fx=self.fx,
            fy=self.fy,
            cx=self.cx - offset_x,
            cy=self.cy - offset_y,
            skew=self.skew,
            distortion=self.distortion.copy(),
            source=self.source,
            state=self.state,
            original_width=self.original_width,
            original_height=self.original_height,
            resize_scale_x=self.resize_scale_x,
            resize_scale_y=self.resize_scale_y,
            crop_offset_x=self.crop_offset_x + offset_x,
            crop_offset_y=self.crop_offset_y + offset_y,
            reprojection_rmse_px=self.reprojection_rmse_px,
        )

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "schema_version": "1.0",
            "camera_model": self.model_type.value,
            "image_width": self.width,
            "image_height": self.height,
            "fx": self.fx,
            "fy": self.fy,
            "cx": self.cx,
            "cy": self.cy,
            "skew": self.skew,
            "distortion": self.distortion,
            "source": self.source.value,
            "calibration_state": self.state.value,
            "original_width": self.original_width,
            "original_height": self.original_height,
        }
        if self.reprojection_rmse_px is not None:
            d["reprojection_rmse_px"] = self.reprojection_rmse_px
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CameraModel":
        w = data["image_width"]
        h = data["image_height"]
        fx = data["fx"]
        fy = data.get("fy", fx)
        cx = data.get("cx", w / 2.0)
        cy = data.get("cy", h / 2.0)
        dist = data.get("distortion", [])
        if not isinstance(dist, list):
            dist = []

        if not all(np.isfinite([w, h, fx, fy, cx, cy])):
            raise ValueError("Invalid non-finite parameters in camera intrinsics.")
        if fx <= 0 or fy <= 0:
            raise ValueError("Focal length must be strictly positive.")

        return cls(
            model_type=CameraModelType(data.get("camera_model", "PINHOLE")),
            width=int(w),
            height=int(h),
            fx=float(fx),
            fy=float(fy),
            cx=float(cx),
            cy=float(cy),
            skew=float(data.get("skew", 0.0)),
            distortion=[float(x) for x in dist],
            source=CalibrationSource(data.get("source", CalibrationSource.APPROXIMATED.value)),
            state=CalibrationState(data.get("calibration_state", CalibrationState.UNKNOWN.value)),
            reprojection_rmse_px=data.get("reprojection_rmse_px"),
        )


class Undistorter:
    def __init__(self, camera: CameraModel):
        self.camera = camera
        self.map_x: Optional[np.ndarray] = None
        self.map_y: Optional[np.ndarray] = None
        self.undistorted_camera: Optional[CameraModel] = None

    def _init_maps(self):
        if self.map_x is not None and self.map_y is not None:
            return

        dist = self.camera.to_opencv_distortion()
        K = self.camera.to_matrix()

        # We assume the undistorted image has the same resolution,
        # but we use getOptimalNewCameraMatrix to preserve all pixels if desired,
        # or we just map using the original K (which might crop edges).
        # Let's map using the original K to keep geometry consistent unless specified otherwise.

        new_K = K.copy()
        # For simplicity, we just keep the camera matrix the same to preserve principal point,
        # but OpenCV allows computing a new one.
        if np.any(dist):
            if self.camera.model_type == CameraModelType.OPENCV_FISHEYE:
                new_K = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(
                    K, dist[:4], (self.camera.width, self.camera.height), np.eye(3)
                )
                self.map_x, self.map_y = cv2.fisheye.initUndistortRectifyMap(
                    K, dist[:4], np.eye(3), new_K, (self.camera.width, self.camera.height), cv2.CV_32FC1
                )
            else:
                self.map_x, self.map_y = cv2.initUndistortRectifyMap(
                    K, dist, np.eye(3), new_K, (self.camera.width, self.camera.height), cv2.CV_32FC1
                )
        else:
            # Identity map
            self.map_x, self.map_y = np.meshgrid(
                np.arange(self.camera.width, dtype=np.float32), np.arange(self.camera.height, dtype=np.float32)
            )

        self.undistorted_camera = CameraModel(
            model_type=CameraModelType.PINHOLE,
            width=self.camera.width,
            height=self.camera.height,
            fx=new_K[0, 0],
            fy=new_K[1, 1],
            cx=new_K[0, 2],
            cy=new_K[1, 2],
            skew=new_K[0, 1],
            source=self.camera.source,
            state=self.camera.state,
        )

    def undistort_image(self, img: np.ndarray) -> np.ndarray:
        self._init_maps()
        if self.map_x is None or self.map_y is None:
            return img
        return cv2.remap(img, self.map_x, self.map_y, cv2.INTER_LINEAR)

    def get_undistorted_camera(self) -> CameraModel:
        self._init_maps()
        assert self.undistorted_camera is not None
        return self.undistorted_camera
