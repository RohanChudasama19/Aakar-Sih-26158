import requests

js = requests.get("http://127.0.0.1:8000/assets/index-Cux3IcQU.js").text

# Find the navigation after job submission - look for how result is handled
idx = js.find('/api/jobs')
snippet = js[idx:idx+400]
print("POST /api/jobs handler:")
print(snippet)
print()

# Look for id extraction from submit response
for pat in ["result.id", ".id)", "data.id", "json().id", "then(e=>", "then(r=>"]:
    i = js.find(pat, 280000)  # search near the jobs section
    if i >= 0:
        print(f"'{pat}' @ {i}:", js[max(0,i-60):i+80])
        print()
