from pathlib import Path

p = Path("web/app.js")
js = p.read_text(encoding="utf-8")
js = js.replace("if (!leafletMap) {", "if (!window.leafletMap) {")
js = js.replace("leafletMap.invalidateSize();", "window.leafletMap.invalidateSize();")
p.write_text(js, encoding="utf-8")
