import requests

js = requests.get("http://127.0.0.1:8000/assets/index-Cux3IcQU.js").text

# Check key patterns for result.id vs result.job_id navigation bug
checks = [
    ("result.id",          "should exist for correct navigation"),
    ("result.job_id",      "OLD BUG - should NOT exist"),
    ("AeroRecon",          "branding"),
    ("Dashboard",          "Dashboard page"),
    ("Workspace",          "Workspace page"),
    ("Settings",           "Settings page"),
    ("Measurements",       "Measurements"),
    ("dense_cloud",        "dense cloud support"),
    ("mesh.glb",           "GLB viewer"),
    ("mission_report",     "reports"),
    ("PLY",                "PLY downloads"),
    ("GLB",                "GLB downloads"),
]

print("=== BUNDLE CONTENT CHECK ===")
for pat, desc in checks:
    found = pat in js
    print(f"  {pat:30s}: {'FOUND' if found else 'MISSING'}  ({desc})")
