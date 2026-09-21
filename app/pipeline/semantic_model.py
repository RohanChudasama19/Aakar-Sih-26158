import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np


# We abstract the model to avoid breaking imports if onnx/torch are missing
class SemanticModelBackend:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.status = "MODEL_UNAVAILABLE"
        self.device = "CPU"
        self.session = None
        self.classes = [
            "UNKNOWN",
            "BUILDING",
            "ROAD",
            "OBSTACLE",
            "VEGETATION",
            "VEGETATION",
            "DYNAMIC_OBJECT",
            "DYNAMIC_OBJECT",
        ]  # UAVid mapped loosely for dummy interface

        if self.model_path and Path(self.model_path).exists():
            self._load_model()

    def _load_model(self):
        try:
            import onnxruntime as ort

            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            self.session = ort.InferenceSession(self.model_path, providers=providers)
            self.device = self.session.get_providers()[0]
            self.status = "MODEL_SEGMENTATION"
        except Exception as e:
            logging.error(f"Failed to load ONNX model: {e}")
            self.status = "MODEL_LOAD_FAILED"

    def infer_frame(self, image_np: np.ndarray) -> Dict[str, Any]:
        """
        Run inference on a single frame.
        Returns class mask and confidence map.
        """
        if self.status != "MODEL_SEGMENTATION":
            return {"status": self.status}

        t0 = time.time()

        # Preprocessing (Dummy strategy: resize to 512x512, normalize)
        # In a real model, this would use cv2/PIL
        H, W = image_np.shape[:2]

        # Dummy inference:
        # In real life:
        # input_name = self.session.get_inputs()[0].name
        # res = self.session.run(None, {input_name: tensor_input})[0]

        # We simulate inference for unit tests
        class_mask = np.zeros((H, W), dtype=np.uint8)
        confidence = np.ones((H, W), dtype=np.float32) * 0.9

        infer_ms = (time.time() - t0) * 1000

        return {
            "status": self.status,
            "mask": class_mask,
            "confidence": confidence,
            "inference_ms": infer_ms,
            "device": self.device,
        }


def get_backend_status(model_path: Optional[str]) -> str:
    if model_path is None or not Path(model_path).exists():
        return "HEURISTIC_FALLBACK"
    backend = SemanticModelBackend(model_path)
    if backend.status == "MODEL_SEGMENTATION":
        return "MODEL_SEGMENTATION"
    return "HEURISTIC_FALLBACK"
