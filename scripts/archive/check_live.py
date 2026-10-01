import requests, json

base = "http://127.0.0.1:8000"

# 1. Check index.html for friend-designed bundle
idx = requests.get(base + "/").text
bundle_ok = "index-D5QFe07I.js" in idx
print(f"Friend-designed bundle: {'PRESENT' if bundle_ok else 'MISSING'}")
print(f"CDN refs: {'FOUND - PROBLEM' if 'cdn.jsdelivr.net' in idx or 'cdnjs' in idx else 'NONE - OK'}")

# 2. Check the JS for the result.id bug
try:
    js = requests.get(base + "/assets/index-D5QFe07I.js").text[:5000]
    has_job_id = "result.job_id" in js
    has_result_id = "result.id" in js
    print(f"result.id pattern: {'FOUND' if has_result_id else 'NOT FOUND'}")
    print(f"result.job_id bug: {'PRESENT - FIX NEEDED' if has_job_id else 'NOT PRESENT - OK'}")
except Exception as e:
    print(f"JS check error: {e}")

# 3. Jobs list - check MARS appears
jobs = requests.get(base + "/api/jobs").json()
mars = [j for j in jobs if "mars" in j.get("id","")]
colorado = [j for j in jobs if j.get("id","") == "95f51b12-b771-47bf-9201-c3700f9475a7"]
print(f"Total jobs in API: {len(jobs)}")
print(f"MARS job found: {len(mars) > 0}  status={mars[0].get('status') if mars else 'N/A'}")
print(f"Colorado job found: {len(colorado) > 0}  status={colorado[0].get('status') if colorado else 'N/A'}")
