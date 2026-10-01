import requests

js = requests.get("http://127.0.0.1:8000/assets/index-Cux3IcQU.js").text

# Find the New Mission / submit form - look near /new route
for pat in ["/new", "NewMission", "onSubmit", "formData", "FormData"]:
    i = js.find(pat, 280000)
    if i >= 0:
        print(f"'{pat}' @ {i}:")
        print(js[max(0,i-20):i+200])
        print()
