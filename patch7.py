from pathlib import Path

p = Path("app/main.py")
js = p.read_text(encoding="utf-8")
js = js.replace("total = 0", "total = 0\n    print(f'Inside save: {target.name}, passed budget={budget}')")
p.write_text(js, encoding="utf-8")
