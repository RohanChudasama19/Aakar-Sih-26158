import requests

js = requests.get("http://127.0.0.1:8000/assets/index-Cux3IcQU.js").text

# Find submit handler and what it does with the response
idx = js.find("gT()")  # the submit function
if idx < 0:
    idx = js.find("Upload Error")  
snippet_end = idx + 600
snippet = js[max(0,idx-100):snippet_end]
print("Submit / upload handler region:")
print(snippet)
