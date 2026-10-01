import requests

js = requests.get("http://127.0.0.1:8000/assets/index-Cux3IcQU.js").text

# Find the submit callback - what happens after (t) resolves
idx = js.find("Upload Error")
region = js[idx:idx+1000]
print("After upload error check (submission result handling):")
print(region)
