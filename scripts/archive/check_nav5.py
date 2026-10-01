import requests

js = requests.get("http://127.0.0.1:8000/assets/index-Cux3IcQU.js").text

# find FormData section and what follows
idx = js.find('h.append("video"')
region = js[idx:idx+300]
print("FormData build and submit:")
print(region)
