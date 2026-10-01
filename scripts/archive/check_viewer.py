import requests

js = requests.get("http://127.0.0.1:8000/assets/index-Cux3IcQU.js").text

idx = js.find("No representation could be loaded")
snippet = js[max(0,idx-400):idx+200]
print("Viewer loading logic:")
print(snippet)
