import re

code = open('app/main.py', encoding='utf-8').read()

new_handler = '''VALID_SPA_ROUTES = {"", "projects", "new", "workspace", "analytics", "quality", "models", "exports", "settings"}

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: HTTPException):
    path = request.url.path
    if path.startswith("/api/") or path.startswith("/assets/"):
        return JSONResponse({"detail": "Not found"}, status_code=404)
    
    segments = path.strip("/").split("/")
    root_segment = segments[0] if segments else ""
    
    if root_segment in VALID_SPA_ROUTES:
        index = ROOT / "web" / "index.html"
        if index.exists():
            return FileResponse(index)
            
    return JSONResponse({"detail": "Not found"}, status_code=404)
'''

# Find the old handler
code = re.sub(r'@app\.exception_handler\(404\).*?return FileResponse\(index\)', new_handler, code, flags=re.DOTALL)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Updated SPA 404 handler.")
