"""Incremental calibrated SfM. Points are accepted only with positive depth and parallax."""

import cv2
import numpy as np


def matches(a, b):
    if a is None or b is None or len(a) < 2 or len(b) < 2:
        return []
    pairs = cv2.BFMatcher().knnMatch(a, b, k=2)
    candidates = sorted(
        [m for pair in pairs if len(pair) == 2 for m, n in [pair] if m.distance < 0.72 * n.distance],
        key=lambda m: m.distance,
    )
    seen, out = set(), []
    for m in candidates:
        if m.trainIdx not in seen:
            out.append((m.queryIdx, m.trainIdx))
            seen.add(m.trainIdx)
    return out


def triangulate(k, pa, pb, xa, xb):
    p = cv2.triangulatePoints(k @ pa, k @ pb, xa.T, xb.T)
    xyz = (p[:3] / np.where(abs(p[3]) > 1e-10, p[3], np.nan)).T
    ca, cb = -pa[:, :3].T @ pa[:, 3], -pb[:, :3].T @ pb[:, 3]
    va, vb = xyz - ca, xyz - cb
    cos = np.sum(va * vb, axis=1) / (np.linalg.norm(va, axis=1) * np.linalg.norm(vb, axis=1) + 1e-12)
    angle = np.degrees(np.arccos(np.clip(cos, -1, 1)))
    good = np.isfinite(xyz).all(axis=1) & (angle > 0.7) & (angle < 80)
    for pose, obs in [(pa, xa), (pb, xb)]:
        cam = xyz @ pose[:, :3].T + pose[:, 3]
        pix = cam @ k.T
        projected = pix[:, :2] / np.where(abs(pix[:, 2:3]) > 1e-10, pix[:, 2:3], np.nan)
        good &= (cam[:, 2] > 0) & (np.linalg.norm(projected - obs, axis=1) < 2.5)
    return xyz, good


def reconstruct(directory, info, k, notify):
    cv2.setRNGSeed(42)
    sift = cv2.SIFT_create(nfeatures=5000)
    frames = info["frames"]
    keypoints, descriptors, images = [], [], []
    for f in frames:
        im = cv2.imread(str(directory / f["name"]))
        mask = cv2.imread(str(directory.parent / "masks" / (f["name"] + ".png")), 0)
        kp, d = sift.detectAndCompute(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), mask)
        keypoints.append(np.array([x.pt for x in kp], dtype=np.float64).reshape(-1, 2))
        descriptors.append(d)
        images.append(cv2.imread(str(directory.parent / "originals" / f["name"])))
    best = None
    for a in range(min(3, len(frames) - 1)):
        for b in range(a + 1, min(len(frames), a + 7)):
            mm = matches(descriptors[a], descriptors[b])
            if len(mm) < 30:
                continue
            ia, ib = np.array(mm).T
            xa, xb = keypoints[a][ia], keypoints[b][ib]
            e, mask = cv2.findEssentialMat(xa, xb, k, method=cv2.RANSAC, prob=0.999, threshold=1.0)
            if e is None or e.shape != (3, 3):
                continue
            _, r, t, mask = cv2.recoverPose(e, xa, xb, k, mask=mask)
            pa, pb = np.c_[np.eye(3), np.zeros(3)], np.c_[r, t]
            xyz, good = triangulate(k, pa, pb, xa, xb)
            good &= mask.ravel() > 0
            score = int(good.sum())
            if best is None or score > best[0]:
                best = score, a, b, pa, pb, xyz, good, ia, ib
    if best is None or best[0] < 25:
        raise ValueError(
            "SfM failed: insufficient verified parallax/matches. Pure rotation, flat textureless scenes, and duplicate frames cannot determine 3D."
        )
    _, a, b, pa, pb, xyz, good, ia, ib = best
    points = list(xyz[good])
    colors = []
    observations = [dict() for _ in frames]
    for pid, (ka, kb) in enumerate(zip(ia[good], ib[good])):
        observations[a][int(ka)] = pid
        observations[b][int(kb)] = pid
        u, v = np.rint(keypoints[a][ka]).astype(int)
        colors.append(images[a][v, u, ::-1])
    poses = {a: pa, b: pb}
    for _ in range(3):
        added = 0
        for j in range(len(frames)):
            if j in poses:
                continue
            candidate, all_matches = {}, []
            for ref in sorted(poses, key=lambda x: abs(x - j))[:4]:
                mm = matches(descriptors[ref], descriptors[j])
                all_matches.append((ref, mm))
                for x, y in mm:
                    if x in observations[ref]:
                        candidate[y] = observations[ref][x]
            if len(candidate) < 10:
                continue
            idx = list(candidate)
            obj = np.array([points[candidate[x]] for x in idx])
            obs = keypoints[j][idx]
            ok, rv, tv, inliers = cv2.solvePnPRansac(
                obj, obs, k, None, iterationsCount=300, reprojectionError=3.0, confidence=0.999, flags=cv2.SOLVEPNP_EPNP
            )
            if not ok or inliers is None or len(inliers) < 10:
                continue
            ii = inliers.ravel()
            rv, tv = cv2.solvePnPRefineLM(obj[ii], obs[ii], k, None, rv, tv)
            r, _ = cv2.Rodrigues(rv)
            poses[j] = np.c_[r, tv]
            added += 1
            for q in ii:
                observations[j][idx[q]] = candidate[idx[q]]
            for ref, mm in all_matches:
                fresh = [(x, y) for x, y in mm if x not in observations[ref] and y not in observations[j]]
                if len(fresh) < 4:
                    continue
                ka, kb = np.array(fresh).T
                xyz, valid = triangulate(k, poses[ref], poses[j], keypoints[ref][ka], keypoints[j][kb])
                for p, x, y in zip(xyz[valid], ka[valid], kb[valid]):
                    if x in observations[ref] or y in observations[j]:
                        continue
                    pid = len(points)
                    points.append(p)
                    observations[ref][int(x)] = pid
                    observations[j][int(y)] = pid
                    u, v = np.rint(keypoints[j][y]).astype(int)
                    colors.append(images[j][v, u, ::-1])
            notify(
                20 + 20 * len(poses) / len(frames),
                f"Registered {len(poses)}/{len(frames)} cameras; {len(points)} triangulated points",
            )
        if not added:
            break
    if len(poses) < 3:
        raise ValueError("Only two cameras registered; stable multi-frame reconstruction needs at least three")
    points = np.asarray(points)
    errors = []
    for j, pose in poses.items():
        ids = list(observations[j])
        pids = [observations[j][x] for x in ids]
        cam = points[pids] @ pose[:, :3].T + pose[:, 3]
        pix = cam @ k.T
        errors.extend(np.linalg.norm(pix[:, :2] / pix[:, 2:3] - keypoints[j][ids], axis=1).tolist())
    return {
        "points": points,
        "colors": np.asarray(colors),
        "poses": poses,
        "reprojection_rmse_px": float(np.sqrt(np.mean(np.square(errors)))),
        "engine": "opencv_incremental_sfm",
    }
