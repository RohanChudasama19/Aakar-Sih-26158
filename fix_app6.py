from pathlib import Path

p = Path("web/app.js")
js = p.read_text(encoding="utf-8")
js = js.replace("/api/jobs//files/mesh/model.glb", "`/api/jobs/${j.id}/files/mesh/model.glb`")
js = "import * as Meas from './measurements.js';\n" + js
p.write_text(js, encoding="utf-8")
