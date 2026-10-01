import requests, json
jm = requests.get('http://127.0.0.1:8000/api/jobs/mars_hkairport01_quality').json()
jc = requests.get('http://127.0.0.1:8000/api/jobs/95f51b12-b771-47bf-9201-c3700f9475a7').json()

print("MARS VIEWER ARTIFACTS:")
print(json.dumps(jm.get("viewer_artifacts"), indent=2))
print("\nCOLORADO VIEWER ARTIFACTS:")
print(json.dumps(jc.get("viewer_artifacts"), indent=2))
