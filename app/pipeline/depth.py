"""Optional custom ONNX depth: NCHW RGB [0,1] -> positive Z-depth [1,1,H,W].
Depth scale is fit to visible sparse geometry. Learned completions remain separate.
"""

import cv2
import numpy as np


def infer(model, sfm, k, directory, out, notify):
    import onnxruntime as ort

    session = ort.InferenceSession(str(model), providers=["CPUExecutionProvider"])
    inp = session.get_inputs()[0]
    h, w = inp.shape[-2:]
    if not isinstance(h, int) or not isinstance(w, int) or min(h, w) < 32 or max(h, w) > 2048:
        raise ValueError("Depth ONNX input requires fixed NCHW spatial dimensions between 32 and 2048")
    points = []
    colors = []
    supported = 0
    for q, j in enumerate(sorted(sfm["poses"])[::3]):
        image = cv2.imread(str(directory / f"{j:06d}.png"))
        raw = cv2.cvtColor(cv2.resize(image, (w, h)), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
        depth = np.squeeze(session.run(None, {inp.name: raw.transpose(2, 0, 1)[None]})[0])
        if depth.ndim != 2 or not np.isfinite(depth).all():
            raise ValueError("Depth model must return a finite 2D positive Z-depth map")
        depth = cv2.resize(depth, (image.shape[1], image.shape[0]))
        pose = sfm["poses"][j]
        r, t = pose[:, :3], pose[:, 3]
        cam = sfm["points"] @ r.T + t
        pix = cam @ k.T
        uv = np.rint(pix[:, :2] / np.maximum(pix[:, 2:3], 1e-8)).astype(int)
        good = (
            (cam[:, 2] > 0)
            & (uv[:, 0] >= 0)
            & (uv[:, 0] < image.shape[1])
            & (uv[:, 1] >= 0)
            & (uv[:, 1] < image.shape[0])
        )
        if good.sum() < 20:
            continue
        uv = uv[good]
        z = cam[good, 2]
        pred = depth[uv[:, 1], uv[:, 0]]
        keep = pred > 1e-5
        if keep.sum() < 20:
            continue
        scale = np.median(z[keep] / pred[keep])
        relative = np.median(abs(scale * pred[keep] - z[keep]) / z[keep])
        if relative > 0.25:
            continue
        yy, xx = np.mgrid[0 : image.shape[0] : 8, 0 : image.shape[1] : 8]
        z = depth[::8, ::8] * scale
        rays = np.c_[xx.ravel(), yy.ravel(), np.ones(xx.size)] @ np.linalg.inv(k).T
        camera = rays * z.ravel()[:, None]
        valid = (z.ravel() > 0) & np.isfinite(camera).all(1)
        mask = cv2.imread(str(directory.parent / "masks" / f"{j:06d}.png.png"), 0)
        valid &= mask[::8, ::8].ravel() > 0
        points.append(((camera - t) @ r)[valid])
        colors.append(image[::8, ::8, ::-1].reshape(-1, 3)[valid])
        supported += 1
    p = np.concatenate(points) if points else np.empty((0, 3))
    c = np.concatenate(colors) if colors else np.empty((0, 3), np.uint8)
    np.savez_compressed(
        out / "inferred_depth_regions.npz", points_sfm=p, colors=c, evidence=np.full(len(p), "inferred")
    )
    return {
        "frames_scale_aligned": supported,
        "inferred_points": len(p),
        "fused_into_measured_mesh": False,
        "note": "Learned depth is retained separately to avoid treating single-view estimates as measured surfaces.",
    }
