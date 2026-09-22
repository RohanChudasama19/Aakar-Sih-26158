import json
import logging
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

logger = logging.getLogger(__name__)


class SemanticBackendState(str, Enum):
    MODEL_SEGMENTATION = "MODEL_SEGMENTATION"
    HEURISTIC_FALLBACK = "HEURISTIC_FALLBACK"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    MODEL_LOAD_FAILED = "MODEL_LOAD_FAILED"


class AeroReconClass(str, Enum):
    BUILDING = "BUILDING"
    ROAD = "ROAD"
    VEGETATION = "VEGETATION"
    OBSTACLE = "OBSTACLE"
    DYNAMIC_OBJECT = "DYNAMIC_OBJECT"
    UNKNOWN = "UNKNOWN"


class UAVidClass(int, Enum):
    CLUTTER = 0  # [0, 0, 0]
    BUILDING = 1  # [128, 0, 0]
    ROAD = 2  # [128, 64, 128]
    STATIC_CAR = 3  # [192, 0, 192]
    TREE = 4  # [0, 128, 0]
    LOW_VEGETATION = 5  # [128, 128, 0]
    HUMAN = 6  # [64, 64, 0]
    MOVING_CAR = 7  # [64, 0, 128]


UAVID_TO_AERORECON = {
    UAVidClass.BUILDING: AeroReconClass.BUILDING,
    UAVidClass.ROAD: AeroReconClass.ROAD,
    UAVidClass.TREE: AeroReconClass.VEGETATION,
    UAVidClass.LOW_VEGETATION: AeroReconClass.VEGETATION,
    UAVidClass.STATIC_CAR: AeroReconClass.OBSTACLE,
    UAVidClass.MOVING_CAR: AeroReconClass.DYNAMIC_OBJECT,
    UAVidClass.HUMAN: AeroReconClass.DYNAMIC_OBJECT,
    UAVidClass.CLUTTER: AeroReconClass.UNKNOWN,
}


class SemanticPipeline:
    def __init__(self, model_path: Optional[Path] = None):
        self.state = SemanticBackendState.MODEL_UNAVAILABLE
        self.model_path = model_path
        self.session = None
        self.input_name = ""
        self.output_name = ""
        self.device = "cpu"
        self.inference_time_ms = 0.0

        if model_path is not None and model_path.exists():
            self._load_onnx_model(model_path)
        else:
            logger.warning("ONNX model not found. Defaulting to HEURISTIC_FALLBACK.")
            self.state = SemanticBackendState.HEURISTIC_FALLBACK

    def _load_onnx_model(self, path: Path):
        try:
            import onnxruntime as ort

            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            self.session = ort.InferenceSession(str(path), providers=providers)
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name

            # Check actual provider
            active_providers = self.session.get_providers()
            if "CUDAExecutionProvider" in active_providers:
                self.device = "cuda"
            else:
                self.device = "cpu"

            self.state = SemanticBackendState.MODEL_SEGMENTATION
            logger.info(f"Loaded semantic model from {path} on {self.device}")
        except ImportError:
            logger.error("onnxruntime not installed. Falling back to heuristics.")
            self.state = SemanticBackendState.MODEL_LOAD_FAILED
        except Exception as e:
            logger.error(f"Failed to load ONNX model {path}: {e}")
            self.state = SemanticBackendState.MODEL_LOAD_FAILED

    def get_status(self) -> Dict[str, Any]:
        return {
            "model_name": "LRASPP-MobileNetV3-Large",
            "version": "1.0",
            "backend": self.state.value,
            "device": self.device,
            "classes": [c.name for c in UAVidClass],
            "inference_time_ms": self.inference_time_ms,
            "model_available": self.state == SemanticBackendState.MODEL_SEGMENTATION,
        }

    def infer_image(self, image_np: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Input: RGB image HxWx3 (uint8)
        Output:
            class_mask (HxW, uint8)
            confidence_map (HxW, float32)
            dynamic_candidates (HxW, bool)
        """
        if self.state != SemanticBackendState.MODEL_SEGMENTATION or self.session is None:
            # Fallback
            h, w = image_np.shape[:2]
            return (
                np.full((h, w), UAVidClass.CLUTTER.value, dtype=np.uint8),
                np.zeros((h, w), dtype=np.float32),
                np.zeros((h, w), dtype=bool),
            )

        import time

        # Preprocessing: resize to e.g. 512x1024 or standard size, normalize
        # For this skeleton, we assume dummy processing if no real input is provided
        import cv2

        t0 = time.monotonic()
        h, w = image_np.shape[:2]

        # Standard torchvision normalization
        input_tensor = cv2.resize(image_np, (1024, 512)).astype(np.float32) / 255.0
        input_tensor = (input_tensor - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])
        input_tensor = np.transpose(input_tensor, (2, 0, 1))  # C, H, W
        input_tensor = np.expand_dims(input_tensor, axis=0)  # 1, C, H, W

        # Inference
        outputs = self.session.run([self.output_name], {self.input_name: input_tensor})
        logits = outputs[0][0]  # C, H, W

        probs = np.exp(logits) / np.sum(np.exp(logits), axis=0, keepdims=True)
        class_idx = np.argmax(probs, axis=0).astype(np.uint8)
        confidence = np.max(probs, axis=0).astype(np.float32)

        # Resize back to original
        class_mask = cv2.resize(class_idx, (w, h), interpolation=cv2.INTER_NEAREST)
        confidence_map = cv2.resize(confidence, (w, h), interpolation=cv2.INTER_LINEAR)

        self.inference_time_ms = (time.monotonic() - t0) * 1000.0

        # Dynamic Candidates
        dynamic_mask = (class_mask == UAVidClass.MOVING_CAR.value) | (class_mask == UAVidClass.HUMAN.value)

        return class_mask, confidence_map, dynamic_mask

    def project_2d_to_3d(
        self,
        points_3d: np.ndarray,
        camera_pose: np.ndarray,  # 4x4 matrix
        intrinsics: np.ndarray,  # 3x3 matrix
        class_mask: np.ndarray,
        confidence_map: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Projects semantic labels from a single 2D view onto 3D points using visibility/ray intersection concepts.
        Returns:
            projected_classes: shape (N,)
            projected_confidence: shape (N,)
        """
        # Naive implementation for skeleton
        # In full implementation: apply view angle filtering, depth/z-buffering for occlusion
        # Here we just project using extrinsics/intrinsics.
        N = len(points_3d)
        classes = np.full(N, UAVidClass.CLUTTER.value, dtype=np.uint8)
        confs = np.zeros(N, dtype=np.float32)

        if N == 0:
            return classes, confs

        # P = K [R|t] X
        pts_hom = np.hstack((points_3d, np.ones((N, 1))))
        cam_pts = (camera_pose @ pts_hom.T).T

        # Filter points behind camera
        valid_z = cam_pts[:, 2] > 0

        uv_hom = (intrinsics @ cam_pts[valid_z, :3].T).T
        uv = uv_hom[:, :2] / uv_hom[:, 2:3]
        u = np.round(uv[:, 0]).astype(int)
        v = np.round(uv[:, 1]).astype(int)

        h, w = class_mask.shape
        valid_uv = (u >= 0) & (u < w) & (v >= 0) & (v < h)

        final_valid = np.zeros(N, dtype=bool)
        valid_z_indices = np.where(valid_z)[0]
        final_valid_indices = valid_z_indices[valid_uv]

        u_valid = u[valid_uv]
        v_valid = v[valid_uv]

        classes[final_valid_indices] = class_mask[v_valid, u_valid]
        confs[final_valid_indices] = confidence_map[v_valid, u_valid]

        # View angle confidence penalty could be applied here:
        # e.g., confs *= max(0, dot(ray_dir, surface_normal))

        return classes, confs

    def fuse_multi_view(
        self,
        class_observations: List[np.ndarray],  # List of (N,) arrays
        conf_observations: List[np.ndarray],  # List of (N,) arrays
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Fuses multi-view observations for N 3D points.
        Returns:
            fused_classes (N,)
            fused_confidence (N,)
            view_support_count (N,)
        """
        if not class_observations:
            return np.array([]), np.array([]), np.array([])

        N = len(class_observations[0])
        num_classes = len(UAVidClass)

        # Accumulate weighted votes
        votes = np.zeros((N, num_classes), dtype=np.float32)
        support = np.zeros(N, dtype=np.int32)

        for c_obs, conf_obs in zip(class_observations, conf_observations):
            valid_mask = conf_obs > 0
            support[valid_mask] += 1
            # Add confidence to the voted class
            for i in range(N):
                if valid_mask[i]:
                    votes[i, c_obs[i]] += conf_obs[i]

        fused_classes = np.argmax(votes, axis=1).astype(np.uint8)

        # Avoid division by zero
        safe_support = np.maximum(support, 1)
        fused_confidence = np.max(votes, axis=1) / safe_support

        # Default to Clutter if no support
        fused_classes[support == 0] = UAVidClass.CLUTTER.value
        fused_confidence[support == 0] = 0.0

        return fused_classes, fused_confidence, support

    def temporally_confirm_dynamics(self, dynamic_candidates: List[np.ndarray]) -> np.ndarray:
        """
        Takes dynamic masks from multiple frames and applies optical flow / multi-frame
        consistency to upgrade to TEMPORALLY_CONFIRMED_DYNAMIC.
        """
        # Skeleton: require object to be moving (differ across frames)
        # Simplified: if it overlaps across consecutive frames identically, it might be static.
        # Real implementation uses optical flow or epipolar constraints.
        if not dynamic_candidates:
            return np.array([])
        # For now, just return the logical OR as a placeholder for temporal confirmation
        return np.logical_or.reduce(dynamic_candidates)
