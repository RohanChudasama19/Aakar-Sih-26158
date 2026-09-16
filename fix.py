from pathlib import Path

p = Path("web/index.html")
text = p.read_text(encoding="utf-8")
text = text.replace(
    '<link rel="stylesheet" href="/style.css">',
    '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script><link rel="stylesheet" href="/style.css">'
)
p.write_text(text, encoding="utf-8")
