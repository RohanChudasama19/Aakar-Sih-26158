"""CPU reduced-fidelity dense stereo: calibrated rectification and SGBM."""

import cv2
import numpy as np

from .sfm import triangulate


def cpu_densify(sfm, k, directory, notify, max_pairs=12):
    poses = sfm["poses"]
    ids = sorted(poses)
    pairs = list(zip(ids, ids[2:])) or list(zip(ids, ids[1:]))
    if len(pairs) > max_pairs:
        pairs = [pairs[i] for i in np.linspace(0, len(pairs) - 1, max_pairs).astype(int)]
    points = [sfm["points"]]
    colors = [sfm["colors"]]
    accepted = 0
    flow_accepted = 0
    for q, (a, b) in enumerate(pairs):
        im1 = cv2.imread(str(directory / f"{a:06d}.png"))
        im2 = cv2.imread(str(directory / f"{b:06d}.png"))
        h, w = im1.shape[:2]
        ga = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
        gb = cv2.cvtColor(im2, cv2.COLOR_BGR2GRAY)
        ma = cv2.imread(str(directory.parent / "masks" / f"{a:06d}.png.png"), 0)
        mb = cv2.imread(str(directory.parent / "masks" / f"{b:06d}.png.png"), 0)
        features = cv2.goodFeaturesToTrack(ga, 8000, 0.005, 3, mask=ma)
        if features is not None and len(features) > 20:
            tracked, forward, _ = cv2.calcOpticalFlowPyrLK(ga, gb, features, None, winSize=(21, 21), maxLevel=4)
            back, backward, _ = cv2.calcOpticalFlowPyrLK(gb, ga, tracked, None, winSize=(21, 21), maxLevel=4)
            xa = features.reshape(-1, 2)
            xb = tracked.reshape(-1, 2)
            valid = (
                (forward.ravel() > 0)
                & (backward.ravel() > 0)
                & (np.linalg.norm(back.reshape(-1, 2) - xa, axis=1) < 0.6)
            )
            valid &= (xb[:, 0] >= 1) & (xb[:, 0] < w - 1) & (xb[:, 1] >= 1) & (xb[:, 1] < h - 1)
            pos = np.rint(xb).astype(int)
            valid &= mb[np.clip(pos[:, 1], 0, h - 1), np.clip(pos[:, 0], 0, w - 1)] > 0
            if valid.sum() > 20:
                cloud, good = triangulate(k, poses[a], poses[b], xa[valid].astype(float), xb[valid].astype(float))
                center = np.median(sfm["points"], axis=0)
                radius = np.percentile(np.linalg.norm(sfm["points"] - center, axis=1), 95) * 2
                good &= np.linalg.norm(cloud - center, axis=1) < radius
                points.append(cloud[good])
                uv = np.rint(xa[valid][good]).astype(int)
                colors.append(im1[uv[:, 1], uv[:, 0], ::-1])
                flow_accepted += int(good.sum())
        ra, ta = poses[a][:, :3], poses[a][:, 3]
        rb, tb = poses[b][:, :3], poses[b][:, 3]
        r = rb @ ra.T
        t = tb - r @ ta
        r1, r2, p1, p2, Q, _, _ = cv2.stereoRectify(
            k,
            None,
            k,
            None,
            (w, h),
            np.ascontiguousarray(r),
            np.ascontiguousarray(t.reshape(3, 1)),
            flags=cv2.CALIB_ZERO_DISPARITY,
            alpha=0,
        )
        # OpenCV SGBM searches horizontal positive disparity only.
        if abs(p2[1, 3]) > abs(p2[0, 3]) or p2[0, 3] >= 0:
            continue
        map1 = cv2.initUndistortRectifyMap(k, None, r1, p1, (w, h), cv2.CV_32FC1)
        map2 = cv2.initUndistortRectifyMap(k, None, r2, p2, (w, h), cv2.CV_32FC1)
        left = cv2.remap(im1, *map1, cv2.INTER_LINEAR)
        right = cv2.remap(im2, *map2, cv2.INTER_LINEAR)
        nd = min(128, max(16, ((w // 4) // 16) * 16))
        stereo = cv2.StereoSGBM_create(
            minDisparity=0,
            numDisparities=nd,
            blockSize=5,
            P1=8 * 25,
            P2=32 * 25,
            disp12MaxDiff=1,
            uniquenessRatio=12,
            speckleWindowSize=100,
            speckleRange=2,
            mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY,
        )
        disp = (
            stereo.compute(cv2.cvtColor(left, cv2.COLOR_BGR2GRAY), cv2.cvtColor(right, cv2.COLOR_BGR2GRAY)).astype(
                float
            )
            / 16
        )
        xyz = cv2.reprojectImageTo3D(disp.astype(np.float32), Q)
        valid = (disp > 1) & (disp < nd - 2) & np.isfinite(xyz).all(2) & (xyz[:, :, 2] > 0)
        mask = cv2.imread(str(directory.parent / "masks" / f"{a:06d}.png.png"), 0)
        valid &= cv2.remap(mask, *map1, cv2.INTER_NEAREST) > 0
        right_mask = cv2.imread(str(directory.parent / "masks" / f"{b:06d}.png.png"), 0)
        right_mask = cv2.remap(right_mask, *map2, cv2.INTER_NEAREST)
        yy, xx = np.indices((h, w))
        xr = np.rint(xx - disp).astype(int)
        valid &= (xr >= 0) & (xr < w)
        valid &= right_mask[yy, np.clip(xr, 0, w - 1)] > 0
        reverse = cv2.StereoSGBM_create(
            minDisparity=-nd,
            numDisparities=nd,
            blockSize=5,
            P1=8 * 25,
            P2=32 * 25,
            uniquenessRatio=12,
            speckleWindowSize=100,
            speckleRange=2,
        )
        dr = (
            reverse.compute(cv2.cvtColor(right, cv2.COLOR_BGR2GRAY), cv2.cvtColor(left, cv2.COLOR_BGR2GRAY)).astype(
                float
            )
            / 16
        )
        valid &= abs(disp + dr[yy, np.clip(xr, 0, w - 1)]) < 1.5
        sampler = np.zeros((h, w), bool)
        sampler[::4, ::4] = True
        valid &= sampler
        camera = xyz[valid] @ r1
        world = (camera - ta) @ ra
        if len(world):
            # Reject stereo points far outside the supported sparse scene envelope.
            center = np.median(sfm["points"], axis=0)
            radius = np.percentile(np.linalg.norm(sfm["points"] - center, axis=1), 95) * 2
            keep = np.linalg.norm(world - center, axis=1) < radius
            points.append(world[keep])
            colors.append(left[valid][keep, ::-1])
            accepted += int(keep.sum())
        notify(43 + 15 * (q + 1) / len(pairs), f"Dense stereo pair {q + 1}/{len(pairs)}; {accepted} supported samples")
    xyz = np.concatenate(points)
    rgb = np.concatenate(colors)
    size = max(np.linalg.norm(np.ptp(xyz, axis=0)) / 500, 1e-5)
    _, idx = np.unique(np.floor(xyz / size).astype(np.int64), axis=0, return_index=True)
    return (
        xyz[idx],
        rgb[idx],
        {
            "stereo_points": accepted,
            "tracked_stereo_points": flow_accepted,
            "method": "calibrated_SGBM_and_bidirectional_LK",
            "neural_completion": False,
        },
    )
