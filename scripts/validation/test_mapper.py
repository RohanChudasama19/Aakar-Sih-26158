import subprocess
db = "workspace/HKairport01_FAST_C_FINAL/inputs/colmap.db"
p = subprocess.run([
    r"C:\Tools\COLMAP\bin\colmap.exe", "mapper",
    "--database_path", db,
    "--image_path", "workspace/HKairport01_FAST_C_FINAL/inputs/images",
    "--output_path", "workspace/HKairport01_FAST_C_FINAL/work/sparse_test",
    "--Mapper.init_image_id1", "1",
    "--Mapper.init_image_id2", "2",
], stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
print(p.stdout)
print(p.stderr)
