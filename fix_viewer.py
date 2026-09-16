import re
from pathlib import Path

p = Path("web/viewer.js")
js = p.read_text(encoding="utf-8")

# 1. Add onMeasureUpdate and measureMeshes
js = js.replace("let measureMode = 'orbit', measurePoints = [], measureLine = null;", "let measureMode = 'orbit', measurePoints = [], measureMeshes = [];\n  const onMeasureUpdate = options.onMeasureUpdate || (() => {});")

# 2. Update pointerup to call _drawMeasure without the old sphere logic (since we'll put it in _drawMeasure)
ptr_logic_old = '''    measurePoints.push(hit.point.clone());
    const marker = new THREE.Mesh(
      new THREE.SphereGeometry(cameraSize / 280, 12, 8),
      new THREE.MeshBasicMaterial({ color: 0xc6ff8e, depthTest: false })
    );
    marker.position.copy(hit.point);
    marker.renderOrder = 11;
    annotations.add(marker);
    _drawMeasure();'''

ptr_logic_new = '''    measurePoints.push(hit.point.clone());
    _drawMeasure();'''

js = js.replace(ptr_logic_old, ptr_logic_new)

# 3. Replace _clearMeasure and _drawMeasure completely
clear_start = js.find("function _clearMeasure() {")
draw_end = js.find("}\n", js.find("function _drawMeasure() {")) + 2
# Wait, _drawMeasure has an if/else block inside it. Let's find it reliably by finding the next function "window.getCurrentViewerType"
draw_end = js.find("window.getCurrentViewerType")

new_funcs = '''function _clearMeasure() {
    for (const o of [...annotations.children]) {
      annotations.remove(o);
      o.geometry?.dispose();
      o.material?.dispose();
    }
    measurePoints = [];
    measureMeshes = [];
    if (measureMode !== 'orbit') onMeasureUpdate(measurePoints, measureMode);
  }

  function _drawMeasure() {
    for (const o of measureMeshes) {
      annotations.remove(o);
      o.geometry?.dispose();
      o.material?.dispose();
    }
    measureMeshes = [];

    // Draw markers
    for (let i = 0; i < measurePoints.length; i++) {
        const marker = new THREE.Mesh(
          new THREE.SphereGeometry(cameraSize / 280, 12, 8),
          new THREE.MeshBasicMaterial({ color: 0xc6ff8e, depthTest: false })
        );
        marker.position.copy(measurePoints[i]);
        marker.renderOrder = 11;
        annotations.add(marker);
        measureMeshes.push(marker);
    }

    if (measurePoints.length > 1) {
        if (measureMode === 'area' && measurePoints.length > 2) {
            const path = [...measurePoints, measurePoints[0]];
            const line = new THREE.Line(
              new THREE.BufferGeometry().setFromPoints(path),
              new THREE.LineBasicMaterial({ color: 0xc6ff8e, depthTest: false })
            );
            line.renderOrder = 10;
            annotations.add(line);
            measureMeshes.push(line);
        } else {
            const line = new THREE.Line(
              new THREE.BufferGeometry().setFromPoints(measurePoints),
              new THREE.LineBasicMaterial({ color: 0xc6ff8e, depthTest: false })
            );
            line.renderOrder = 10;
            annotations.add(line);
            measureMeshes.push(line);
        }
    }
    
    onMeasureUpdate(measurePoints, measureMode);
  }

  '''

js = js[:clear_start] + new_funcs + js[draw_end:]

# Remove measureLabel references
js = js.replace("const measureLabel = options.measureLabel || { textContent: '' };\n", "")
js = js.replace("measureLabel.textContent = 'Select points on the model';", "")
js = js.replace("      measureLabel.textContent =\n        v === 'orbit' ? 'Drag to explore' :\n        v === 'area'  ? 'Select polygon corners in order on one plane' :\n        'Select points to measure a path';", "")


p.write_text(js, encoding="utf-8")
