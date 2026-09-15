# mypy: ignore-errors
import math
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

# Default configurable thresholds
CONFIG: Dict[str, Any] = {
    "sampling": {
        "window_duration_sec": 5.0,  # Temporal window size
        "frames_per_window": 3,  # Base frames to sample per window
        "analysis_width_px": 960,  # Standardized width for blur/exposure/features
    },
    "integrity": {
        "min_frames": 30,  # Hard minimum frames
    },
    "blur": {
        "warning_threshold": 40.0,  # Laplacian variance at analysis_width_px
        "block_ratio": 0.5,  # Block if 50% frames are blurry
    },
    "exposure": {
        "dark_threshold": 30,  # Pixel value considered shadow-clipped
        "bright_threshold": 225,  # Pixel value considered highlight-clipped
        "warning_clipped_ratio": 0.4,  # Warn if 40% of pixels in a frame are clipped
        "block_dark_frame_ratio": 0.7,
    },
    "features": {
        "warning_count": 200,  # Minimum features expected
        "grid_size": (4, 4),  # Grid for spatial distribution
        "warning_occupancy": 0.3,  # Warn if features are in < 30% of grid cells
    },
    "overlap": {
        "min_inliers": 30,
        "warning_inliers": 80,
        "max_local_distance": 3,  # Check pairs up to i -> i+3
    },
    "parallax": {
        "warning_angular_deg": 1.0,  # Degrees
        "warning_proxy": 5.0,  # Pixels (normalized space)
    },
    "connectivity": {
        "block_largest_cc_ratio": 0.5,  # Block if the largest connected component is < 50% of sampled frames
    },
    "motion": {
        "jump_threshold_px": 100,  # LK flow abrupt jump
        "near_zero_px": 2.0,
    },
    "telemetry": {
        "max_gps_gap_sec": 3.0,
        "max_speed_mps": 35.0,  # Excessive speed jump
    },
}


def compute_exposure(gray: np.ndarray, config: Dict) -> Dict:
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).ravel()
    total = gray.size
    shadows = np.sum(hist[: config["dark_threshold"]]) / total
    highlights = np.sum(hist[config["bright_threshold"] :]) / total
    mean_lum = float(np.mean(gray))
    median_lum = float(np.median(gray))
    is_dark = shadows > config["warning_clipped_ratio"] or median_lum < config["dark_threshold"]
    is_bright = highlights > config["warning_clipped_ratio"] or median_lum > config["bright_threshold"]
    return {
        "mean_luminance": mean_lum,
        "median_luminance": median_lum,
        "shadow_clipped_ratio": float(shadows),
        "highlight_clipped_ratio": float(highlights),
        "is_dark": is_dark,
        "is_overexposed": is_bright,
    }


def compute_features(gray: np.ndarray, config: Dict) -> Tuple[list, np.ndarray, Dict]:
    try:
        detector = cv2.SIFT_create(nfeatures=2000)
        detector_type = "SIFT"
    except Exception:
        detector = cv2.ORB_create(nfeatures=2000)
        detector_type = "ORB"

    kps, des = detector.detectAndCompute(gray, None)
    if kps is None:
        kps, des = [], None

    count = len(kps)
    # Compute spatial occupancy
    grid_y, grid_x = config["grid_size"]
    h, w = gray.shape
    cells = set()
    for kp in kps:
        x, y = kp.pt
        cx = min(grid_x - 1, int((x / w) * grid_x))
        cy = min(grid_y - 1, int((y / h) * grid_y))
        cells.add((cx, cy))

    occupancy = len(cells) / (grid_x * grid_y)
    is_concentrated = occupancy < config["warning_occupancy"]

    return (
        kps,
        des,
        {"detector": detector_type, "count": count, "occupancy_ratio": occupancy, "is_concentrated": is_concentrated},
    )


def compute_pair_geometry(kp1, kp2, des1, des2, K: np.ndarray) -> Dict:
    if des1 is None or des2 is None or len(kp1) < 10 or len(kp2) < 10:
        return {"inliers": 0}

    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)
    good = []
    for m in matches:
        if len(m) == 2 and m[0].distance < 0.75 * m[1].distance:
            good.append(m[0])

    if len(good) < 10:
        return {"inliers": 0, "matches": len(good)}

    pts1 = np.float32([kp1[m.queryIdx].pt for m in good])
    pts2 = np.float32([kp2[m.trainIdx].pt for m in good])

    # Homography
    H, h_mask = cv2.findHomography(pts1, pts2, cv2.RANSAC, 5.0)
    h_inliers = int(np.sum(h_mask)) if h_mask is not None else 0

    # Fundamental / Essential
    if K is not None:
        E, e_mask = cv2.findEssentialMat(pts1, pts2, K, cv2.RANSAC, 0.99, 1.0)  # type: ignore
        e_inliers = int(np.sum(e_mask)) if e_mask is not None else 0
        inliers = e_inliers
        mask = e_mask
        model_used = "Essential"
    else:
        F, f_mask = cv2.findFundamentalMat(pts1, pts2, cv2.FM_RANSAC, 3.0, 0.99)
        f_inliers = int(np.sum(f_mask)) if f_mask is not None else 0
        inliers = f_inliers
        mask = f_mask
        model_used = "Fundamental"

    parallax_val = 0.0
    parallax_type = "parallax_proxy"

    if inliers > 10 and mask is not None:
        mask_bool = mask.ravel().astype(bool)
        v_pts1 = pts1[mask_bool]
        v_pts2 = pts2[mask_bool]
        if K is not None:
            # Normalized coordinates
            K_inv = np.linalg.inv(K)
            n_pts1 = cv2.perspectiveTransform(v_pts1.reshape(-1, 1, 2), K_inv).reshape(-1, 2)
            n_pts2 = cv2.perspectiveTransform(v_pts2.reshape(-1, 1, 2), K_inv).reshape(-1, 2)
            # Angular parallax (dot product of rays)
            # Rays: [x, y, 1] normalized
            rays1 = np.hstack((n_pts1, np.ones((len(n_pts1), 1))))
            rays2 = np.hstack((n_pts2, np.ones((len(n_pts2), 1))))
            rays1 /= np.linalg.norm(rays1, axis=1)[:, np.newaxis]
            rays2 /= np.linalg.norm(rays2, axis=1)[:, np.newaxis]
            dots = np.sum(rays1 * rays2, axis=1)
            angles = np.arccos(np.clip(dots, -1.0, 1.0))
            parallax_val = float(np.median(angles) * 180.0 / np.pi)
            parallax_type = "parallax_angle"
        else:
            # Pixel displacement of inliers
            parallax_val = float(np.median(np.linalg.norm(v_pts1 - v_pts2, axis=1)))
            parallax_type = "parallax_proxy"

    return {
        "matches": len(good),
        "inliers": inliers,
        "homography_inliers": h_inliers,
        "model_used": model_used,
        "parallax": parallax_val,
        "parallax_type": parallax_type,
        "pure_rotation_risk": (h_inliers > inliers * 0.95 and inliers > 20),
    }


def analyze_telemetry(gps_rows: List[Dict], meta: Dict, config: Dict) -> Dict:
    res = {"warnings": [], "blocking_reasons": []}
    if not gps_rows:
        res["blocking_reasons"].append("Missing mandatory GPS telemetry.")
        return res

    gaps, stationary, outliers = 0, 0, 0
    speeds = []

    for i in range(1, len(gps_rows)):
        prev, curr = gps_rows[i - 1], gps_rows[i]
        dt = curr["time"] - prev["time"]
        if dt > config["max_gps_gap_sec"]:
            gaps += 1
            res["warnings"].append(f"GPS gap of {dt:.1f}s near frame {curr['frame']}.")

        # Simple distance approx
        dy = (curr["latitude"] - prev["latitude"]) * 111000
        dx = (curr["longitude"] - prev["longitude"]) * 111000 * math.cos(math.radians(prev["latitude"]))
        dist = math.hypot(dx, dy)
        speed = dist / dt if dt > 0 else 0
        speeds.append(speed)

        if speed > config["max_speed_mps"]:
            outliers += 1
        elif speed < 0.2:
            stationary += 1

    res["gaps"] = gaps
    res["outliers"] = outliers
    res["stationary"] = stationary
    if gaps > 5 or (len(gps_rows) > 0 and gaps / len(gps_rows) > 0.1):
        res["blocking_reasons"].append("Excessive telemetry gaps.")

    return res


from ..camera import CameraModel


def perform_analysis(
    video_path: Path, gps_rows: List[Dict], meta: Dict, intrinsics: Optional[CameraModel] = None
) -> Dict:
    start_time = time.time()
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return {"status": "NOT_READY", "blocking_reasons": ["Cannot decode video file."]}

    fps = cap.get(cv2.CAP_PROP_FPS)
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w_orig = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    duration = count / fps if fps > 0 else 0

    if count < CONFIG["integrity"]["min_frames"] or fps <= 0:
        return {"status": "NOT_READY", "blocking_reasons": [f"Insufficient frames ({count}) or invalid FPS."]}

    # Stratified temporal sampling
    w_dur = CONFIG["sampling"]["window_duration_sec"]
    frames_per_w = CONFIG["sampling"]["frames_per_window"]
    w_frames = int(w_dur * fps)

    sample_indices = []
    for w_start in range(0, count, w_frames):
        w_end = min(w_start + w_frames, count)
        step = max(1, (w_end - w_start) // frames_per_w)
        for i in range(w_start, w_end, step):
            if i < count:
                sample_indices.append(i)

    sample_indices = sorted(list(set(sample_indices)))

    frames_data = []
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    current_idx = 0

    for idx in sample_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, raw = cap.read()
        if not ok:
            continue

        # Analysis resolution
        scale = CONFIG["sampling"]["analysis_width_px"] / raw.shape[1]
        img = cv2.resize(raw, None, fx=scale, fy=scale) if scale < 1.0 else raw
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        exposure = compute_exposure(gray, CONFIG["exposure"])
        kps, des, feats = compute_features(gray, CONFIG["features"])

        frames_data.append(
            {
                "index": idx,
                "sharpness": sharpness,
                "exposure": exposure,
                "features": feats,
                "_kps": kps,
                "_des": des,
                "_gray": gray,
            }
        )

    cap.release()

    if len(frames_data) < 3:
        return {"status": "NOT_READY", "blocking_reasons": ["Could not extract enough valid frames."]}

    # Edge graph
    edges = []
    n = len(frames_data)
    max_dist = CONFIG["overlap"]["max_local_distance"]
    K_scaled = None
    if intrinsics is not None:
        scaled_cam = intrinsics.scale(
            CONFIG["sampling"]["analysis_width_px"],
            int(intrinsics.height * (CONFIG["sampling"]["analysis_width_px"] / intrinsics.width)),
        )
        K_scaled = scaled_cam.to_matrix()

    for i in range(n):
        for j in range(i + 1, min(i + 1 + max_dist, n)):
            geom = compute_pair_geometry(
                frames_data[i]["_kps"], frames_data[j]["_kps"], frames_data[i]["_des"], frames_data[j]["_des"], K_scaled
            )
            edges.append({"from": i, "to": j, "geom": geom})

    # Graph connectivity
    adj = {i: [] for i in range(n)}
    for e in edges:
        if e["geom"]["inliers"] >= CONFIG["overlap"]["min_inliers"]:
            adj[e["from"]].append(e["to"])
            adj[e["to"]].append(e["from"])

    visited = set()
    ccs = []
    for i in range(n):
        if i not in visited:
            cc = set()
            queue = [i]
            while queue:
                node = queue.pop(0)
                if node not in cc:
                    cc.add(node)
                    visited.add(node)
                    queue.extend([nbr for nbr in adj[node] if nbr not in cc])
            ccs.append(cc)

    largest_cc = len(max(ccs, key=len)) if ccs else 0
    lcc_ratio = largest_cc / n
    isolated = len([c for c in ccs if len(c) == 1]) / n

    # Telemetry
    telem_report = analyze_telemetry(gps_rows, meta, CONFIG["telemetry"])

    # Aggregation
    blur_ratio = sum(1 for f in frames_data if f["sharpness"] < CONFIG["blur"]["warning_threshold"]) / n
    dark_ratio = sum(1 for f in frames_data if f["exposure"]["is_dark"]) / n
    conc_ratio = sum(1 for f in frames_data if f["features"]["is_concentrated"]) / n

    warnings = telem_report.get("warnings", [])
    blocking = telem_report.get("blocking_reasons", [])
    positive = []

    if blur_ratio > CONFIG["blur"]["block_ratio"]:
        blocking.append(f"Excessive blur ({blur_ratio * 100:.1f}% frames blurry).")
    elif blur_ratio > 0.1:
        warnings.append(f"Moderate blur detected ({blur_ratio * 100:.1f}% frames blurry).")

    if lcc_ratio < CONFIG["connectivity"]["block_largest_cc_ratio"]:
        blocking.append(f"Disconnected dataset. Largest contiguous segment is only {lcc_ratio * 100:.1f}%.")
    else:
        positive.append(f"Good dataset connectivity ({lcc_ratio * 100:.1f}% in main component).")

    avg_inliers = np.mean([e["geom"]["inliers"] for e in edges if e["to"] == e["from"] + 1]) if edges else 0

    # Motion and redundancy (using parallax and match counts)
    near_zero = 0
    jumps = 0
    pure_rotation = 0
    for e in edges:
        if e["to"] == e["from"] + 1:
            g = e["geom"]
            if g["parallax"] < 1.0 and g["inliers"] > 50:
                near_zero += 1
            if g["pure_rotation_risk"]:
                pure_rotation += 1
            if g["inliers"] < 10 and g["matches"] > 0:
                jumps += 1

    if near_zero / n > 0.3:
        warnings.append(f"High redundancy: {near_zero / n * 100:.1f}% of consecutive frames have near-zero motion.")
    if pure_rotation / n > 0.3:
        warnings.append(f"Risk of pure rotation without baseline in {pure_rotation / n * 100:.1f}% of frame pairs.")
    if jumps > 0:
        warnings.append(f"Abrupt jumps or lost tracking detected in {jumps} pairs.")

    if avg_inliers < CONFIG["overlap"]["warning_inliers"]:
        warnings.append(f"Low sequential overlap (avg {avg_inliers:.1f} inliers).")

    status = "READY"
    if blocking:
        status = "NOT_READY"
    elif warnings:
        status = "WARNING"

    score = 100.0
    if blur_ratio > 0:
        score -= blur_ratio * 30
    if lcc_ratio < 1.0:
        score -= (1.0 - lcc_ratio) * 50
    if dark_ratio > 0.2:
        score -= dark_ratio * 20
    score = max(0.0, score)
    if status == "NOT_READY":
        score = min(score, 40.0)

    # Clean up non-serializable fields
    for f in frames_data:
        f.pop("_kps", None)
        f.pop("_des", None)
        f.pop("_gray", None)

    report = {
        "schema_version": "1.0",
        "analyzer_version": "0.1.0",
        "mission": {"total_frames": count, "fps": fps, "duration_sec": duration},
        "sampling": {"sampled_frames": n, "strategy": "stratified_temporal"},
        "image_quality": {"blur_ratio": blur_ratio, "dark_ratio": dark_ratio},
        "connectivity": {"largest_component_ratio": lcc_ratio, "isolated_ratio": isolated},
        "redundancy": {"near_zero_motion_ratio": near_zero / n if n > 0 else 0},
        "motion": {"pure_rotation_risk_ratio": pure_rotation / n if n > 0 else 0, "jumps": jumps},
        "telemetry": telem_report,
        "scores": {"overall_readiness_score": score},
        "status": status,
        "blocking_reasons": blocking,
        "warnings": warnings,
        "positive_evidence": positive,
        "recommendations": [],
        "runtime": time.time() - start_time,
        "frames": frames_data,
        "edges": edges,
        "config": CONFIG,
    }

    if "blur" in " ".join(blocking + warnings).lower():
        report["recommendations"].append("Use faster shutter speed or slower UAV motion.")
    if "overlap" in " ".join(blocking + warnings).lower() or "Disconnected" in " ".join(blocking):
        report["recommendations"].append(
            "Reduce frame sampling interval or capture with more continuous scene overlap."
        )

    return report
