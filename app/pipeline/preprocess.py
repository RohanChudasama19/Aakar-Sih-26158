import json

import cv2
import numpy as np

DYNAMIC_CLASSES = {0, 1, 2, 3, 5, 7, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23}


def extract(video, out, options, notify):
    out.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise ValueError("Cannot decode video; use an H.264 MP4")
    fps = cap.get(cv2.CAP_PROP_FPS)
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    source_size = [int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))]
    if fps <= 0 or count < 3:
        raise ValueError("Video contains fewer than three frames or no valid frame rate")
    detector = None
    if options.get("semantic_pipeline"):
        from app.pipeline.semantic_model import SemanticPipeline

        detector = SemanticPipeline()
    records, rejected, masked, last, i = [], 0, 0, None, 0
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    limit = int(options.get("max_frames", 180))
    min_gap = max(1, int(count / (limit * 5)))
    while True:
        ok, raw = cap.read()
        if not ok:
            break
        index = i
        i += 1
        if index % min_gap:
            continue
        scale = min(1.0, float(options.get("max_width", 960)) / raw.shape[1])
        raw = cv2.resize(raw, None, fx=scale, fy=scale)
        gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if sharpness < float(options.get("blur_threshold", 40)):
            rejected += 1
            continue
        motion = 100.0
        if last is not None:
            pts = cv2.goodFeaturesToTrack(last, 300, 0.01, 8)
            if pts is not None and len(pts) >= 12:
                nxt, st, _ = cv2.calcOpticalFlowPyrLK(last, gray, pts, None)
                good = st.ravel().astype(bool)
                motion = float(np.median(np.linalg.norm(nxt[good] - pts[good], axis=2))) if good.sum() > 10 else 100.0
            if motion < float(options.get("motion_px", 12)) and index - records[-1]["frame"] < fps * 1.5:
                continue
        name = f"{len(records):06d}.png"
        original_dir = out.parent / "originals"
        original_dir.mkdir(exist_ok=True)
        cv2.imwrite(str(original_dir / name), raw)
        mask = np.full(gray.shape, 255, np.uint8)
        if detector is not None:
            # Semantic Pipeline inference
            _, _, dyn_mask = detector.infer_image(raw)
            if np.any(dyn_mask):
                mask[dyn_mask] = 0
                masked += 1
        lab = cv2.cvtColor(raw, cv2.COLOR_BGR2LAB)
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        normalized = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        normalized[mask == 0] = 0
        cv2.imwrite(str(out / name), normalized)
        mask_dir = out.parent / "masks"
        mask_dir.mkdir(exist_ok=True)
        cv2.imwrite(str(mask_dir / (name + ".png")), mask)
        records.append(
            {
                "name": name,
                "frame": index,
                "time_sec": index / fps,
                "sharpness": sharpness,
                "motion_px": motion,
                "masked_fraction": float(np.mean(mask == 0)),
            }
        )
        last = gray
        if len(records) % 10 == 0:
            notify(min(18.0, 18 * index / count), f"Selected {len(records)} frames; decoding {index}/{count}")
        if len(records) >= limit:
            break
    cap.release()
    if len(records) < 3:
        raise ValueError("Insufficient sharp, nonduplicate frames. Use textured scenery and lateral camera motion.")
    result = {
        "frames": records,
        "source_resolution": source_size,
        "input_frames": count,
        "fps": fps,
        "duration_sec": count / fps,
        "blur_rejections": rejected,
        "masked_detections": masked,
        "dynamic_masking": detector is not None,
        "truncated": i < count,
        "width": last.shape[1],
        "height": last.shape[0],
    }
    (out.parent / "preprocess.json").write_text(json.dumps(result, indent=2))
    return result
