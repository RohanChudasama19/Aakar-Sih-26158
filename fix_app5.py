from pathlib import Path

p = Path("web/app.js")
js = p.read_text(encoding="utf-8")
js = js.replace("import * as Meas from './measurements.js';", "")
p.write_text(js, encoding="utf-8")
