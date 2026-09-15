import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def main():
    parser = argparse.ArgumentParser(description="Offline checkerboard camera calibration")
    parser.add_argument("--images", type=str, required=True, help="Directory containing calibration images")
    parser.add_argument("--output", type=str, default="camera_intrinsics.json", help="Output JSON file")
    parser.add_argument("--rows", type=int, default=6, help="Inner corners per row")
    parser.add_argument("--cols", type=int, default=9, help="Inner corners per column")
    parser.add_argument("--square_size", type=float, default=0.025, help="Square size in meters")
    parser.add_argument(
        "--model", type=str, default="OPENCV", choices=["PINHOLE", "RADIAL", "OPENCV", "OPENCV_FISHEYE"]
    )
    args = parser.parse_args()

    images_dir = Path(args.images)
    if not images_dir.exists():
        print(f"Error: {images_dir} does not exist")
        return

    image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
    if not image_files:
        print(f"No images found in {images_dir}")
        return

    objp = np.zeros((args.rows * args.cols, 3), np.float32)
    objp[:, :2] = np.mgrid[0 : args.cols, 0 : args.rows].T.reshape(-1, 2)
    objp *= args.square_size

    objpoints = []
    imgpoints = []
    img_size = None

    print(f"Processing {len(image_files)} images...")
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    for fname in image_files:
        img = cv2.imread(str(fname))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if img_size is None:
            img_size = (gray.shape[1], gray.shape[0])
        elif img_size != (gray.shape[1], gray.shape[0]):
            print(f"Warning: {fname} has a different resolution. Skipping.")
            continue

        ret, corners = cv2.findChessboardCorners(gray, (args.cols, args.rows), None)
        if ret:
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners2)

    valid = len(objpoints)
    if valid < 3:
        print("Error: insufficient valid checkerboard detections")
        return

    print(f"Calibrating using {valid} valid images...")

    flags = 0
    if args.model == "PINHOLE":
        flags |= (
            cv2.CALIB_ZERO_TANGENT_DIST
            | cv2.CALIB_FIX_K1
            | cv2.CALIB_FIX_K2
            | cv2.CALIB_FIX_K3
            | cv2.CALIB_FIX_K4
            | cv2.CALIB_FIX_K5
            | cv2.CALIB_FIX_K6
        )
    elif args.model == "RADIAL":
        flags |= cv2.CALIB_ZERO_TANGENT_DIST | cv2.CALIB_FIX_K3 | cv2.CALIB_FIX_K4 | cv2.CALIB_FIX_K5 | cv2.CALIB_FIX_K6

    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, img_size, None, None, flags=flags)

    # OpenCV returned distortion is [k1, k2, p1, p2, k3]
    distortion = dist.ravel().tolist()

    if args.model == "PINHOLE":
        distortion = []
    elif args.model == "RADIAL":
        distortion = distortion[:2]

    out = {
        "schema_version": "1.0",
        "camera_model": args.model,
        "image_width": img_size[0],
        "image_height": img_size[1],
        "fx": float(mtx[0, 0]),
        "fy": float(mtx[1, 1]),
        "cx": float(mtx[0, 2]),
        "cy": float(mtx[1, 2]),
        "distortion": distortion,
        "source": "SELF_CALIBRATED",
        "calibration_state": "CALIBRATED",
        "reprojection_rmse_px": float(ret),
        "calibration_info": {
            "images_used": valid,
            "total_images": len(image_files),
            "board": f"{args.cols}x{args.rows}",
        },
    }

    out_path = Path(args.output)
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Calibration successful! RMSE: {ret:.3f} px")
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
