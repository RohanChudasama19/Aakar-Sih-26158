import re
from pathlib import Path

p = Path("web/app.js")
js = p.read_text(encoding="utf-8")

new_createViewer = '''    viewer = await createViewer(
      viewerContainer,
      j.id,
      reps || { textured: { available: true, url: /api/jobs//files/mesh/model.glb } },
      metric,
      {
         onMeasureUpdate: (pts, mode) => {
             if (window._handleMeasureUpdate) window._handleMeasureUpdate(pts, mode);
         }
      }
    );'''

js = re.sub(r'viewer = await createViewer\([^;]*\);', new_createViewer, js)

p.write_text(js, encoding="utf-8")
