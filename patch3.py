from pathlib import Path

p = Path("app/main.py")
js = p.read_text(encoding="utf-8")
js = js.replace("remaining -= await save(", "print(f'Remaining before {filename}: {remaining}'); remaining -= await save(")
p.write_text(js, encoding="utf-8")
