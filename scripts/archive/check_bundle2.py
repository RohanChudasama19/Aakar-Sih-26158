import requests

js = requests.get("http://127.0.0.1:8000/assets/index-Cux3IcQU.js").text

# Minified bundle - search for actual API call patterns
patterns = [
    "/api/jobs",
    "job_id",
    ".id",
    "navigate",
    "completed",
    "dense",
    "mesh",
    "texture",
    "point",
    "Three",
    "three",
    "WebGL",
    "canvas",
    "viewer",
    "sih",
    "aakar",
    "AAKAR",
]

for pat in patterns:
    idx = js.find(pat)
    if idx >= 0:
        snippet = js[max(0,idx-30):idx+60].replace('\n','').replace('\r','')
        print(f"'{pat}' @ {idx}: ...{snippet}...")
    else:
        print(f"'{pat}': NOT FOUND")
