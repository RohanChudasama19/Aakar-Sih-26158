import requests

js = requests.get("http://127.0.0.1:8000/assets/index-Cux3IcQU.js").text

# Find how the submit form calls  and navigates
idx = js.find("handleSubmit")
if idx >= 0:
    print("handleSubmit @ ", idx)
    print(js[idx:idx+400])
    print()

# Look for the onSubmit callback
for pat in ["await ", ".then(", "result=", "res=", "/workspace/", "/mission/"]:
    i = js.find(pat)
    while i >= 0 and i < len(js):
        ctx = js[max(0,i-40):i+100]
        if "job" in ctx.lower() or "submit" in ctx.lower() or "upload" in ctx.lower() or "navigate" in ctx.lower():
            print(f"'{pat}' @ {i}:", ctx)
            print()
        i = js.find(pat, i+1)
        if i > 295000:
            break
