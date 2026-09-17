import tempfile
from pathlib import Path

import cv2
import numpy as np
import trimesh

from app.pipeline.texture import texture_mesh


def test_texture_occlusion():
    # A scene with two walls, one in front of the other.
    # Camera 0 looks straight at Wall 1. Wall 2 is behind Wall 1.
    # Wall 1 should occlude Wall 2.

    vertices = np.array(
        [
            # Wall 1 (Z=10, X from -1 to 1, Y from -1 to 1) - Front wall
            [-1, -1, 10],
            [1, -1, 10],
            [1, 1, 10],
            [-1, 1, 10],
            # Wall 2 (Z=20, X from -1 to 1, Y from -1 to 1) - Back wall
            [-1, -1, 20],
            [1, -1, 20],
            [1, 1, 20],
            [-1, 1, 20],
        ]
    )

    faces = np.array(
        [
            [0, 1, 2],
            [0, 2, 3],  # Wall 1
            [4, 5, 6],
            [4, 6, 7],  # Wall 2
        ]
    )

    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)

    geo = {"metric_state": "RELATIVE", "translation": np.zeros(3), "rotation": np.eye(3), "scale": 1.0}

    # Camera at origin looking +Z
    sfm = {"poses": {0: np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]], dtype=float)}}

    # Standard intrinsic
    k = np.array([[1000, 0, 500], [0, 1000, 500], [0, 0, 1]], dtype=float)

    with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            cv2.imwrite(str(tdp / "000000.png"), np.full((1000, 1000, 3), 255, np.uint8))
            (tdp.parent / "masks").mkdir(exist_ok=True)

            textured = texture_mesh(mesh, geo, sfm, k, tdp, options={"occlusion_test": True})
            assert abs(textured.metadata["textured_face_fraction"] - 0.5) < 1e-5
