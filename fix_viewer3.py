import re
from pathlib import Path

p = Path("web/viewer.js")
js = p.read_text(encoding="utf-8")

ptr_move = '''
  renderer.domElement.addEventListener('pointermove', e => {
      if (measureMode === 'surface_area' && _measureStart && e.buttons === 1) {
          const rect = renderer.domElement.getBoundingClientRect();
          mouse.set((e.clientX - rect.left) / rect.width * 2 - 1, -(e.clientY - rect.top) / rect.height * 2 + 1);
          ray.setFromCamera(mouse, camera);
          const hit = ray.intersectObjects(targets, true)[0];
          if (hit && hit.face && hit.object && hit.object.geometry && hit.object.geometry.attributes.position) {
              const pos = hit.object.geometry.attributes.position;
              const a = new THREE.Vector3().fromBufferAttribute(pos, hit.face.a).applyMatrix4(hit.object.matrixWorld);
              const b = new THREE.Vector3().fromBufferAttribute(pos, hit.face.b).applyMatrix4(hit.object.matrixWorld);
              const c = new THREE.Vector3().fromBufferAttribute(pos, hit.face.c).applyMatrix4(hit.object.matrixWorld);
              
              const centroid = new THREE.Vector3().addVectors(a, b).add(c).divideScalar(3);
              const exists = measureFaces.some(f => {
                  const fc = new THREE.Vector3().addVectors(f[0], f[1]).add(f[2]).divideScalar(3);
                  return fc.distanceTo(centroid) < 1e-5;
              });
              if (!exists) {
                  measureFaces.push([a, b, c]);
                  _drawMeasure();
              }
          }
      }
  });
'''

# insert before pointerup
js = js.replace("  renderer.domElement.addEventListener('pointerup', e => {", ptr_move + "\n  renderer.domElement.addEventListener('pointerup', e => {")
p.write_text(js, encoding="utf-8")
