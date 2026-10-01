import requests

js = requests.get("http://127.0.0.1:8000/assets/index-Cux3IcQU.js").text

idx = js.find("Kt(")
while idx >= 0:
    print(js[max(0,idx-200):idx+100])
    print()
    idx = js.find("Kt(", idx+1)
