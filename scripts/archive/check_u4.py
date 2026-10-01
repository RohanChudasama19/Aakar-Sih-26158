import requests

js = requests.get("http://127.0.0.1:8000/assets/index-Cux3IcQU.js").text

idx = js.find("u4(")
while idx >= 0:
    print(js[max(0,idx-150):idx+250])
    print()
    idx = js.find("u4(", idx+1)
