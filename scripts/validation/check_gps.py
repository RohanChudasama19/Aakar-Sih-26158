import csv
from pathlib import Path

rtk_csv = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon\data_external\uavscenes\raw\HKairport01\metadata\rtk_positions_raw.csv")
with open(rtk_csv) as f:
    reader = csv.DictReader(f)
    rtk_uav = list(reader)

gps_bag = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon\workspace\HKairport01_FAST_C_FINAL\inputs\gps.csv")
with open(gps_bag) as f:
    reader = csv.DictReader(f)
    gps_data = list(reader)

print(f"GPS Bag rows: {len(gps_data)}")
print(f"First GPS Bag: {gps_data[0]}")
print(f"First UAV RTK: {rtk_uav[0]}")
