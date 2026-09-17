from pathlib import Path

p = Path("app/main.py")
js = p.read_text(encoding="utf-8")
js = js.replace("min(remaining, 2 * 1024**2)", "min(remaining, 10 * 1024**2)")
p.write_text(js, encoding="utf-8")
