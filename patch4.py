from pathlib import Path

p = Path("app/main.py")
js = p.read_text(encoding="utf-8")
js = js.replace("raise HTTPException(503, \"Job could not be queued. Check API/Redis logs.\")", "import traceback; traceback.print_exc(); raise HTTPException(503, f\"Job could not be queued. {e}\")")
p.write_text(js, encoding="utf-8")
