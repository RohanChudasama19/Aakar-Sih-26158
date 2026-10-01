import csv
import json
from pathlib import Path

rtk_csv = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon\data_external\uavscenes\raw\HKairport01\metadata\rtk_positions_raw.csv")
with open(rtk_csv) as f:
    reader = csv.DictReader(f)
    rtk_uav = list(reader)

rtk_bag = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon\workspace\HKairport01_FAST_C_FINAL\inputs\rtk.csv")
if rtk_bag.exists():
    with open(rtk_bag) as f:
        reader = csv.DictReader(f)
        rtk_bag_data = list(reader)
    print(f"Bag RTK rows: {len(rtk_bag_data)}")
    print(f"First bag RTK: {rtk_bag_data[0]}")
    print(f"First UAV RTK: {rtk_uav[0]}")
else:
    print("Bag RTK not extracted in inputs!")
