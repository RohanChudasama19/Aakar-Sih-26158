import requests

js = requests.get("http://127.0.0.1:8000/assets/index-Cux3IcQU.js").text

# Find the navigation after successful submit
idx = js.find("const f=await")
region = js[idx:idx+200]
print("Submit result -> navigate:")
print(region)
