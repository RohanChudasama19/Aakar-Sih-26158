import json
import shutil

import cv2
import numpy as np

from .profiles import FAST_QUALITY_V1

DYNAMIC_CLASSES = {0, 1, 2, 3, 5, 7, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23}


def extract(video, out, options, gps_rows, meta, k_test, notify):
    from app.pipeline.readiness import CONFIG, compute_exposure, compute_features, evaluate_extracted

    out.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise ValueError("Cannot decode video")
    fps = cap.get(cv2.CAP_PROP_FPS)
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    source_size = [int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))]

    detector = None
    if options.get("semantic_pipeline"):
        from app.pipeline.semantic_model import SemanticPipeline

        detector = SemanticPipeline()

    candidates = []
    frames_data = []
    rejected = 0
    masked = 0

    # 1. ADAPTIVE CANDIDATE FRAME BANK
    is_fast = options.get("profile") == "FAST_QUALITY"
    cand_target = FAST_QUALITY_V1["candidate_budget"] if is_fast else int(options.get("max_frames", 180) * 2.5)

    min_gap = max(1, int(count / cand_target))

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    last = None

    original_dir = out.parent / "originals"
    original_dir.mkdir(exist_ok=True)
    mask_dir = out.parent / "masks"
    mask_dir.mkdir(exist_ok=True)

    i = 0
    decoded_count = 0
    while True:
        if i % min_gap != 0:
            ok = cap.grab()
            if not ok:
                break
        else:
            ok, raw = cap.read()
            if not ok:
                break
            decoded_count += 1
            index = i

            scale = min(1.0, float(options.get("max_width", 1600)) / raw.shape[1])
            raw = cv2.resize(raw, None, fx=scale, fy=scale)
            gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
            sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

            analysis_scale = CONFIG["sampling"]["analysis_width_px"] / raw.shape[1]
            if analysis_scale < 1.0:
                gray_analysis = cv2.resize(gray, None, fx=analysis_scale, fy=analysis_scale)
            else:
                gray_analysis = gray

            exposure = compute_exposure(gray_analysis, CONFIG["exposure"])
            kps, des, feats = compute_features(gray_analysis, CONFIG["features"])

            frames_data.append(
                {
                    "index": index,
                    "sharpness": sharpness,
                    "exposure": exposure,
                    "features": feats,
                    "_kps": kps,
                    "_des": des,
                    "_gray": gray_analysis,
                }
            )

            if sharpness < float(options.get("blur_threshold", 40)):
                rejected += 1
                i += 1
                continue

            motion = 100.0
            if last is not None:
                pts = cv2.goodFeaturesToTrack(last, 300, 0.01, 8)
                if pts is not None and len(pts) >= 12:
                    nxt, st, _ = cv2.calcOpticalFlowPyrLK(last, gray, pts, None)
                    good = st.ravel().astype(bool)
                    if good.sum() > 10:
                        motion = float(np.median(np.linalg.norm(nxt[good] - pts[good], axis=2)))

            name = f"{index:06d}.png"
            cv2.imwrite(str(original_dir / name), raw)

            mask = np.full(gray.shape, 255, np.uint8)
            if detector is not None:
                _, _, dyn_mask = detector.infer_image(raw)
                if np.any(dyn_mask):
                    mask[dyn_mask] = 0
                    masked += 1

            lab = cv2.cvtColor(raw, cv2.COLOR_BGR2LAB)
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            normalized = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            normalized[mask == 0] = 0

            cand_dir = out.parent / "candidates"
            cand_dir.mkdir(exist_ok=True)
            cv2.imwrite(str(cand_dir / name), normalized)
            cv2.imwrite(str(mask_dir / (name + ".png")), mask)

            candidates.append(
                {
                    "name": name,
                    "frame": index,
                    "time_sec": index / fps,
                    "sharpness": sharpness,
                    "motion_px": motion,
                    "masked_fraction": float(np.mean(mask == 0)),
                    "data_idx": len(frames_data) - 1,
                }
            )
            last = gray
            if len(candidates) % 20 == 0:
                notify(min(10.0, 10 * index / count), f"Extracted {len(candidates)} candidates")
        i += 1

    cap.release()

    ready_report = evaluate_extracted(frames_data, gps_rows, meta, k_test)
    if ready_report["status"] == "NOT_READY" and not is_fast:
        return ready_report, None

    # 2. ADAPTIVE SFM SELECTION
    sfm_target = FAST_QUALITY_V1["sfm_budget"] if is_fast else int(options.get("max_frames", 250))
    if len(candidates) <= sfm_target:
        selected = candidates
    else:
        # Use graph connectivity from ready_report if available to preserve bridge frames
        edges = ready_report.get("_edges", [])
        if edges:
            selected_indices = set([0, len(candidates) - 1])
            # Select target based on sharpness and motion
            remaining = candidates[1:-1]
            step = len(remaining) / max(1, (sfm_target - 2))
            for j in range(sfm_target - 2):
                idx_start = int(j * step)
                idx_end = int((j + 1) * step)
                chunk = remaining[idx_start:idx_end]
                if chunk:
                    best = max(chunk, key=lambda x: x["sharpness"] * min(1.0, max(0.1, x["motion_px"]) / 20.0))
                    selected_indices.add(candidates.index(best))

            # Bridge frame reinsertion
            # Simple heuristic: if the gap between selected frames is too large, insert bridge
            sorted_idx = sorted(list(selected_indices))
            for k in range(len(sorted_idx) - 1):
                curr, nxt = sorted_idx[k], sorted_idx[k + 1]
                if nxt - curr > (len(candidates) / sfm_target) * 3:
                    # Reinsert middle frame
                    selected_indices.add((curr + nxt) // 2)

            selected = [candidates[idx] for idx in sorted(list(selected_indices))]
        else:
            selected = []
            selected.append(candidates[0])
            remaining = candidates[1:-1]
            step = len(remaining) / max(1, (sfm_target - 2))
            for j in range(sfm_target - 2):
                idx_start = int(j * step)
                idx_end = int((j + 1) * step)
                chunk = remaining[idx_start:idx_end]
                if chunk:
                    best = max(chunk, key=lambda x: x["sharpness"] * min(1.0, max(0.1, x["motion_px"]) / 20.0))
                    selected.append(best)
            selected.append(candidates[-1])

    for f in selected:
        shutil.copy(str(out.parent / "candidates" / f["name"]), str(out / f["name"]))

    result = {
        "frames": selected,
        "candidate_count": len(candidates),
        "source_resolution": source_size,
        "input_frames": count,
        "decoded_frames": decoded_count,
        "fps": fps,
        "duration_sec": count / fps,
        "blur_rejections": rejected,
        "masked_detections": masked,
        "dynamic_masking": detector is not None,
        "truncated": False,
        "width": source_size[0],
        "height": source_size[1],
    }
    (out.parent / "preprocess.json").write_text(json.dumps(result, indent=2))
    return ready_report, result
