from pathlib import Path

p = Path("web/app.js")
js = p.read_text(encoding="utf-8")
p.write_text(js.replace("import * as Meas from './measurements.js';\n", ""), encoding="utf-8")
