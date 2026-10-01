import requests

js = requests.get("http://127.0.0.1:8000/assets/index-Cux3IcQU.js").text

idx = js.find('return await Kt("textured",n)')
print(js[max(0,idx-400):idx+200])
