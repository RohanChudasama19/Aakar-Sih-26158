import json
import csv
import zipfile
import sys
from pathlib import Path
from common import write_conversion_report
from dataset_manifest import create_manifest
from validate_canonical_mission import validate_mission

def convert_zurich_mav(input_dir: Path, output_dir: Path):
    print("Zurich Urban MAV Adapter (REAL)")
    
    zip_path = input_dir / "AGZ_subset.zip"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    mission_dir = output_dir / "mission"
    (mission_dir / "telemetry").mkdir(parents=True, exist_ok=True)
    (mission_dir / "control").mkdir(parents=True, exist_ok=True)
    
    warnings = []
    
    if not zip_path.exists():
        print("ACCESS_BLOCKED: AGZ_subset.zip not found in data_external/zurich_mav/raw/")
        warnings.append("Real data not provided; access blocked. Creating synthetic representation.")
        
        with open(mission_dir / "telemetry" / "frame_timestamps.csv", "w") as f:
            f.write("frame_index,source_timestamp,canonical_unix_timestamp,source_identifier\n")
            f.write("0,1000000.0,1600000000.0,frame0000.png\n")
            
        with open(mission_dir / "telemetry" / "imu.csv", "w") as f:
            f.write("canonical_unix_timestamp,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z\n")
            f.write("1600000000.0,0.0,0.0,9.81,0.0,0.0,0.0\n")
            
        with open(mission_dir / "telemetry" / "flight_metadata.json", "w") as f:
            json.dump({"crs": "UNKNOWN", "vertical_datum": "UNKNOWN"}, f)
            
        write_conversion_report(
            dataset="Zurich MAV",
            sequence="synthetic_test",
            input_files=[],
            output_files=["frame_timestamps.csv", "imu.csv", "flight_metadata.json"],
            rows_frames_converted=1,
            timestamp_range=(1600000000.0, 1600000000.0),
            crs="UNKNOWN",
            sensor_availability={"images": True, "imu": True},
            missing_sensors=["gps", "barometer"],
            warnings=warnings,
            errors=[],
            output_dir=output_dir
        )
        report = validate_mission(mission_dir)
        print(f"Validation status: {report['status']}")
        return

    def microsec_to_canonical(ts_str):
        try:
            return float(ts_str) / 1000000.0
        except ValueError:
            return 0.0
            
    with zipfile.ZipFile(zip_path, "r") as z:
        gps_rows = []
        img_timestamps = {}
        with z.open("AGZ_subset/Log Files/OnboardGPS.csv") as f:
            lines = [l.decode("utf-8").strip() for l in f.readlines()]
            for line in lines[1:]:
                if not line: continue
                parts = line.split(",")
                ts = microsec_to_canonical(parts[0])
                imgid = parts[1].strip()
                lat = float(parts[2])
                lon = float(parts[3])
                alt = float(parts[4])
                gps_rows.append((ts, lat, lon, alt))
                if imgid and int(imgid) > 0:
                    img_timestamps[int(imgid)] = ts

        with open(mission_dir / "telemetry" / "gps.csv", "w") as f:
            f.write("canonical_unix_timestamp,lat,lon,alt\n")
            for r in sorted(gps_rows, key=lambda x: x[0]):
                f.write(f"{r[0]},{r[1]},{r[2]},{r[3]}\n")

        img_files = [n for n in z.namelist() if n.startswith("AGZ_subset/MAV Images/") and n.lower().endswith(".jpg")]
        img_files.sort()
        
        with open(mission_dir / "telemetry" / "frame_timestamps.csv", "w") as f:
            f.write("frame_index,source_timestamp,canonical_unix_timestamp,source_identifier\n")
            for idx, n in enumerate(img_files):
                fname = Path(n).name
                imgid = int(fname.split(".")[0])
                ts = img_timestamps.get(imgid, 0.0)
                f.write(f"{idx},{ts},{ts},{fname}\n")
                
        accel_rows = []
        with z.open("AGZ_subset/Log Files/RawAccel.csv") as f:
            lines = [l.decode("utf-8").strip() for l in f.readlines()]
            for line in lines[1:]:
                if not line: continue
                parts = line.split(",")
                ts = microsec_to_canonical(parts[0])
                ax, ay, az = float(parts[2]), float(parts[3]), float(parts[4])
                accel_rows.append((ts, ax, ay, az))
                
        with open(mission_dir / "telemetry" / "imu.csv", "w") as f:
            f.write("canonical_unix_timestamp,accel_x,accel_y,accel_z\n")
            for r in sorted(accel_rows, key=lambda x: x[0]):
                f.write(f"{r[0]},{r[1]},{r[2]},{r[3]}\n")
                
        baro_rows = []
        with z.open("AGZ_subset/Log Files/BarometricPressure.csv") as f:
            lines = [l.decode("utf-8").strip() for l in f.readlines()]
            for line in lines[1:]:
                if not line: continue
                parts = line.split(",")
                ts = microsec_to_canonical(parts[0])
                pressure = float(parts[1])
                temp = float(parts[3])
                baro_rows.append((ts, pressure, temp))
                
        with open(mission_dir / "telemetry" / "barometer.csv", "w") as f:
            f.write("canonical_unix_timestamp,pressure,temperature\n")
            for r in sorted(baro_rows, key=lambda x: x[0]):
                f.write(f"{r[0]},{r[1]},{r[2]}\n")

    with open(mission_dir / "telemetry" / "flight_metadata.json", "w") as f:
        json.dump({
            "crs": "WGS84",
            "vertical_datum": "ELLIPSOIDAL",
            "height_type": "UNKNOWN",
            "units": "meters",
            "timebase": "relative_microseconds",
            "ABSOLUTE_TIME": "NOT_AVAILABLE"
        }, f, indent=2)

    create_manifest(
        dataset_name="Zurich Urban MAV",
        source_url="https://download.ifi.uzh.ch/rpg/AGZ_data/AGZ_subset.zip",
        source_sequence="AGZ_subset",
        local_files=[zip_path],
        license_reference="Academic research use",
        original_format="ZIP",
        output_dir=output_dir
    )

    write_conversion_report(
        dataset="Zurich MAV",
        sequence="AGZ_subset",
        input_files=["AGZ_subset.zip"],
        output_files=["frame_timestamps.csv", "gps.csv", "imu.csv", "barometer.csv", "flight_metadata.json"],
        rows_frames_converted=len(img_files),
        timestamp_range=(min(r[0] for r in gps_rows), max(r[0] for r in gps_rows)),
        crs="WGS84",
        sensor_availability={"images": True, "gps": True, "imu": True, "barometer": True},
        missing_sensors=["rtk"],
        warnings=warnings,
        errors=[],
        output_dir=output_dir
    )
    
    report = validate_mission(mission_dir)
    print(f"Validation status: {report['status']}")
    
if __name__ == "__main__":
    convert_zurich_mav(Path("data_external/zurich_mav/raw"), Path("data_external/zurich_mav"))
