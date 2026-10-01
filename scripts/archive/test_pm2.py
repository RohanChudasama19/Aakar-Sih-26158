import subprocess
import os

env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
cmd = [
    r"C:\Tools\COLMAP\bin\colmap.exe",
    "patch_match_stereo",
    "--workspace_path",
    r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AAKAR-SIH26158-Surface-Fix\aakar\data\95f51b12-b771-47bf-9201-c3700f9475a7\work\dense_fast_quality",
    "--workspace_format",
    "COLMAP",
    "--PatchMatchStereo.config_path",
    r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AAKAR-SIH26158-Surface-Fix\aakar\data\95f51b12-b771-47bf-9201-c3700f9475a7\work\dense_fast_quality\stereo\patch-match-photometric.cfg",
    "--PatchMatchStereo.max_image_size",
    "1600",
    "--PatchMatchStereo.geom_consistency",
    "0",
    "--PatchMatchStereo.window_radius",
    "4",
    "--PatchMatchStereo.window_step",
    "2",
    "--PatchMatchStereo.num_iterations",
    "3"
]
try:
    print("Running...")
    r = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
    print("SUCCESS")
except subprocess.CalledProcessError as e:
    print("FAILED:", e.returncode)
    print("STDOUT:", e.stdout)
    print("STDERR:", e.stderr)
