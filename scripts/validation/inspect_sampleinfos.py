import json
import sys
from pathlib import Path

path = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon\data_external\uavscenes\raw\HKairport01\metadata\sampleinfos_interpolated.json")
if not path.exists():
    print(f"NOT FOUND: {path}")
    sys.exit(1)

with open(path) as f:
    data = json.load(f)

print(f"Top-level type: {type(data).__name__}")
if isinstance(data, list):
    print(f"Entry count: {len(data)}")
    if len(data) > 0:
        first = data[0]
        middle = data[len(data)//2]
        last = data[-1]
        print(f"\nKeys in first entry: {list(first.keys())}")
        
        print("\nFIRST RECORD:")
        print(json.dumps(first, indent=2))
        print("\nMIDDLE RECORD:")
        print(json.dumps(middle, indent=2))
        print("\nLAST RECORD:")
        print(json.dumps(last, indent=2))
        
        # Check poses
        print("\nPose analysis:")
        if "ego2global_translation" in first:
            ts = [d["ego2global_translation"] for d in data]
            print(f"Translations: min={min(ts)}, max={max(ts)}")
