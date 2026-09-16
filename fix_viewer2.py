import re
from pathlib import Path

p = Path("web/viewer.js")
js = p.read_text(encoding="utf-8")

# Let's add measureFaces array
js = js.replace("let measureMode = 'orbit', measurePoints = [], measureMeshes = [];", "let measureMode = 'orbit', measurePoints = [], measureFaces = [], measureMeshes = [];")

# Find the clear function and reset measureFaces
clear_old = '''    measurePoints = [];
    measureMeshes = [];
    if (measureMode !== 'orbit') onMeasureUpdate(measurePoints, measureMode);'''

clear_new = '''    measurePoints = [];
    measureFaces = [];
    measureMeshes = [];
    if (measureMode !== 'orbit') onMeasureUpdate(measureMode === 'surface_area' ? measureFaces : measurePoints, measureMode);'''
js = js.replace(clear_old, clear_new)


# Now pointer up logic
ptr_old = '''    ray.setFromCamera(mouse, camera);
    const hit = ray.intersectObjects(targets, true)[0];
    if (!hit) return;
    
    measurePoints.push(hit.point.clone());
    _drawMeasure();'''

ptr_new = '''    ray.setFromCamera(mouse, camera);
    const hit = ray.intersectObjects(targets, true)[0];
    if (!hit) return;
    
    if (measureMode === 'surface_area') {
        if (hit.face && hit.object && hit.object.geometry && hit.object.geometry.attributes.position) {
            const pos = hit.object.geometry.attributes.position;
            const a = new THREE.Vector3().fromBufferAttribute(pos, hit.face.a).applyMatrix4(hit.object.matrixWorld);
            const b = new THREE.Vector3().fromBufferAttribute(pos, hit.face.b).applyMatrix4(hit.object.matrixWorld);
            const c = new THREE.Vector3().fromBufferAttribute(pos, hit.face.c).applyMatrix4(hit.object.matrixWorld);
            
            // Check if already in measureFaces (by centroid to avoid float issues)
            const centroid = new THREE.Vector3().addVectors(a, b).add(c).divideScalar(3);
            const exists = measureFaces.some(f => {
                const fc = new THREE.Vector3().addVectors(f[0], f[1]).add(f[2]).divideScalar(3);
                return fc.distanceTo(centroid) < 1e-5;
            });
            if (!exists) {
                measureFaces.push([a, b, c]);
            }
        }
    } else {
        measurePoints.push(hit.point.clone());
    }
    _drawMeasure();'''

js = js.replace(ptr_old, ptr_new)


# Now _drawMeasure
draw_old = '''    for (let i = 0; i < measurePoints.length; i++) {
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
    
    onMeasureUpdate(measurePoints, measureMode);'''

draw_new = '''    if (measureMode === 'surface_area') {
        if (measureFaces.length > 0) {
            const positions = new Float32Array(measureFaces.length * 9);
            for (let i = 0; i < measureFaces.length; i++) {
                positions[i*9 + 0] = measureFaces[i][0].x;
                positions[i*9 + 1] = measureFaces[i][0].y;
                positions[i*9 + 2] = measureFaces[i][0].z;
                positions[i*9 + 3] = measureFaces[i][1].x;
                positions[i*9 + 4] = measureFaces[i][1].y;
                positions[i*9 + 5] = measureFaces[i][1].z;
                positions[i*9 + 6] = measureFaces[i][2].x;
                positions[i*9 + 7] = measureFaces[i][2].y;
                positions[i*9 + 8] = measureFaces[i][2].z;
            }
            const geom = new THREE.BufferGeometry();
            geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            
            // Fill
            const mesh = new THREE.Mesh(
                geom,
                new THREE.MeshBasicMaterial({ color: 0xffaa00, transparent: true, opacity: 0.6, side: THREE.DoubleSide })
            );
            mesh.renderOrder = 10;
            annotations.add(mesh);
            measureMeshes.push(mesh);
            
            // Wireframe outline
            const edges = new THREE.LineSegments(
                new THREE.EdgesGeometry(geom),
                new THREE.LineBasicMaterial({ color: 0xffaa00, depthTest: false })
            );
            edges.renderOrder = 11;
            annotations.add(edges);
            measureMeshes.push(edges);
        }
        onMeasureUpdate(measureFaces, measureMode);
    } else {
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
    }'''

js = js.replace(draw_old, draw_new)

p.write_text(js, encoding="utf-8")
