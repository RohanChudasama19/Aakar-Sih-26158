with open("data_external/mars_lvig/raw/ground_truth/Ground Truth/HKairport01_traj.csv", "r") as f:
    lines = f.readlines()
    print("First line:", lines[0].strip())
    print("Last line:", lines[-1].strip())
