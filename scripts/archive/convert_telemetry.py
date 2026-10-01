import csv
import sys

def convert(gt_file, out_file):
    with open(gt_file, "r") as f_in, open(out_file, "w", newline="") as f_out:
        writer = csv.writer(f_out)
        # We output only what we have.
        # AAKAR parser incompatibility: It expects latitude, longitude, altitude_m, compass_heading_deg, etc.
        # We only have relative x, y, z and quaternion qx, qy, qz, qw.
        writer.writerow(["timestamp", "x", "y", "z", "qx", "qy", "qz", "qw"])
        
        for line in f_in:
            line = line.strip()
            if not line: continue
            parts = line.split()
            writer.writerow(parts)

if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2])
