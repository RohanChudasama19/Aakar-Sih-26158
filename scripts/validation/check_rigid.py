import json
import csv
import numpy as np

uav = json.load(open(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon\data_external\uavscenes\raw\HKairport01\metadata\sampleinfos_interpolated.json"))
rtk_data = list(csv.DictReader(open(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon\data_external\uavscenes\raw\HKairport01\metadata\rtk_positions_raw.csv")))

def get_rtk(t):
    for r in rtk_data:
        if abs(float(r["headerstamp"]) - t) < 0.1:
            return np.array([float(r['easting']), float(r['northing']), float(r['alt'])])
    return None

pts_map = []
pts_rtk = []
for d in uav:
    t = float(d["OriginalImageName"].replace(".jpg", ""))
    mx, my, mz = d['T4x4'][0][3], d['T4x4'][1][3], d['T4x4'][2][3]
    rtk = get_rtk(t)
    if rtk is not None:
        pts_map.append([mx, my, mz])
        pts_rtk.append(rtk)

pts_map = np.array(pts_map)
pts_rtk = np.array(pts_rtk)

print(f"Matched {len(pts_map)} poses.")
if len(pts_map) > 0:
    # Compute relative distances between consecutive points
    d_map = np.linalg.norm(np.diff(pts_map, axis=0), axis=1)
    d_rtk = np.linalg.norm(np.diff(pts_rtk, axis=0), axis=1)
    diff = np.abs(d_map - d_rtk)
    print(f"Max scale/distance difference between consecutive frames: {np.max(diff):.5f} m")
    print(f"Mean scale/distance difference: {np.mean(diff):.5f} m")

    # Let's check distance from first point to last point
    dist_map = np.linalg.norm(pts_map[-1] - pts_map[0])
    dist_rtk = np.linalg.norm(pts_rtk[-1] - pts_rtk[0])
    print(f"Total distance Map: {dist_map:.3f} m, RTK: {dist_rtk:.3f} m. Diff: {abs(dist_map - dist_rtk):.3f} m")
