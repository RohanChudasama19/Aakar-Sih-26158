with open("data_external/mars_lvig/raw/ground_truth/Ground Truth/HKairport01_traj.csv") as f:
    lines = f.readlines()
count = 0
for l in lines:
    t = float(l.split()[0])
    if 284940.8 <= t <= 285540.8:
        count += 1
print("GT rows in window:", count)
