import json
from pathlib import Path

path = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon\data_external\uavscenes\raw\HKairport01\metadata\sampleinfos_interpolated.json")
with open(path) as f:
    data = json.load(f)

print([k for k in data[0].keys()])
