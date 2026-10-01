import json
import csv
from pathlib import Path

uav = json.load(open(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AAKAR-SIH26158-Surface-Fix\aakar\data_external\uavscenes\raw\HKairport01\metadata\sampleinfos_interpolated.json"))
rtk_data = list(csv.DictReader(open(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AAKAR-SIH26158-Surface-Fix\aakar\data_external\uavscenes\raw\HKairport01\metadata\rtk_positions_raw.csv")))

def get_rtk(t):
    for r in rtk_data:
        if abs(float(r["headerstamp"]) - t) < 0.1:
            return float(r['easting']), float(r['northing']), float(r['alt'])
    return None

for idx in [0, 3599, 7198]:
    d = uav[idx]
    t = float(d["OriginalImageName"].replace(".jpg", ""))
    mx, my, mz = d['T4x4'][0][3], d['T4x4'][1][3], d['T4x4'][2][3]
    rx, ry, rz = get_rtk(t)
    ox = rx - mx
    oy = ry - my
    oz = rz - mz
    # Wait, Map Z is down if Z is negative when altitude is positive?
    # Let's check rx + mx, or rx - mx.
    # Map Z: -38, RTK alt: 140. 
    # If Map Z is UP, Map Z = -38 is lower than origin (0).
    # If Map Z is UP, then a HIGHER altitude means a MORE POSITIVE Map Z.
    # Let's see: Z went from -38 (first) to 0.84 (middle). So Map Z INCREASED by 39m.
    # Did RTK alt increase?
    print(f"IDX {idx}: Map: {mx:.3f}, {my:.3f}, {mz:.3f} | RTK: {rx:.3f}, {ry:.3f}, {rz:.3f} | Diff: {ox:.3f}, {oy:.3f}, {oz:.3f} | SumZ: {rz+mz:.3f}")
