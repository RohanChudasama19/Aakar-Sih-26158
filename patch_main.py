from pathlib import Path

p = Path("app/main.py")
js = p.read_text(encoding="utf-8")
js = js.replace("raise HTTPException(413, \"Upload exceeds configured byte limit\")", "raise HTTPException(413, f\"Upload exceeds configured byte limit: {total} > {budget} ({target.name})\")")
p.write_text(js, encoding="utf-8")
