from pathlib import Path

p = Path("app/main.py")
js = p.read_text(encoding="utf-8")
js = js.replace("raise HTTPException(503, f\"Job could not be queued. {e}\") from exc", "import traceback; traceback.print_exc(); raise HTTPException(503, f\"Job could not be queued. {exc}\") from exc")
p.write_text(js, encoding="utf-8")
