/**
 * viewer.js â€” AeroRecon Multi-Mode 3D Viewer
 *
 * Supports 6 representation modes:
 *   sparse       â€” Sparse SfM point cloud (PLY)
 *   dense        â€” Dense filtered point cloud (PLY, display artifact)
 *   mesh         â€” Geometry-only mesh (GLB, neutral material)
 *   textured     â€” Textured mesh (GLB, original materials)
 *   semantic     â€” Semantic colored mesh (PLY, class palette)
 *   confidence   â€” Surface support mesh (PLY, support palette)
 *
 * Mode switching:
 *   - Loads existing artifacts only; no reconstruction triggered
 *   - Disposes GPU resources before loading next representation
 *   - Falls back through textured â†’ mesh â†’ dense â†’ sparse
 *
 * Architecture:
 *   createViewer(container, jid, representations, metric, options)
 *   â†’ { loadMode, setMode, clear, dispose, resetView }
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CameraController } from './CameraController.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { PLYLoader } from 'three/addons/loaders/PLYLoader.js';

// â”€â”€ Semantic class palette (mirrors semantic.py SEMANTIC_PALETTE) â”€â”€
const SEMANTIC_PALETTE = {
  0: { name: 'UNKNOWN',        color: '#808080' },
  1: { name: 'GROUND',         color: '#8B4513' },
  2: { name: 'ROAD',           color: '#323232' },
  3: { name: 'BUILDING',       color: '#C83232' },
  4: { name: 'VEGETATION',     color: '#228B22' },
  5: { name: 'WATER',          color: '#0000FF' },
  6: { name: 'INFRASTRUCTURE', color: '#FFA500' },
  7: { name: 'OBSTACLE',       color: '#FFFF00' },
};

// â”€â”€ Confidence/support palette â”€â”€
const CONFIDENCE_PALETTE = {
  SUPPORTED:   { color: '#22C55E', label: 'Supported'   },
  WEAK:        { color: '#EAB308', label: 'Weak'        },
  UNOBSERVED:  { color: '#EF4444', label: 'Unobserved'  },
};

// â”€â”€ API helpers â”€â”€
let _token = '';
export function setViewerToken(t) { _token = t; }
async function fetchBuf(url) {
  const r = await fetch(url, _token ? { headers: { Authorization: `Bearer ${_token}` } } : {});
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${r.url}`);
  return r.arrayBuffer();
}
async function fetchJSON(url) {
  const r = await fetch(url, _token ? { headers: { Authorization: `Bearer ${_token}` } } : {});
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${r.url}`);
  return r.json();
}


/**
 * Create and return a multi-mode 3D viewer.
 *
 * @param {HTMLElement} container  â€” The viewer container element
 * @param {string}      jid        â€” Job ID (for API calls)
 * @param {object}      reps       â€” representations descriptor from /api/jobs/{jid}/representations
 * @param {boolean}     metric     â€” true if metric coordinates available
 * @param {object}      options    â€” { measureLabel: HTMLElement }
 */
export async function createViewer(container, jid, reps, metric, options = {}) {
  // â”€â”€ Three.js setup â”€â”€
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setSize(container.clientWidth, container.clientHeight);
  container.append(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#121b17');

  const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.001, 100000);
  camera.up.set(0, 0, 1);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  const camController = new CameraController(camera, renderer.domElement, controls, () => currentRepObject ? [currentRepObject] : [], msg => { measureLabel.textContent = msg; });
  // Expose virtual joystick
  window.setViewerJoystick = (f, r, u) => camController.setJoystick(f, r, u);
  window.setViewerSpeed = (s) => camController.setSpeed(s);

  // Lights (needed for mesh/textured modes)
  scene.add(new THREE.HemisphereLight(0xffffff, 0x627361, 2.4));
  const dirLight = new THREE.DirectionalLight(0xffffff, 2);
  dirLight.position.set(20, -20, 50);
  scene.add(dirLight);

  // Measurement annotations
  const annotations = new THREE.Group();
  scene.add(annotations);
  const ray = new THREE.Raycaster();
  const mouse = new THREE.Vector2();
  let measureMode = 'orbit', measurePoints = [], measureFaces = [], measureMeshes = [];
  const onMeasureUpdate = options.onMeasureUpdate || (() => {});
  const measureLabel = options.measureLabel || { textContent: '' };
  
  // â”€â”€ State â”€â”€
  let currentRepObject = null;   // current scene object (Points or Group/Mesh)
  let currentMode = null;
  let disposed = false;
  let cameraSize = 10;           // used for marker scaling

  // â”€â”€ Overlay elements â”€â”€
  const loadingEl = _createOverlay(container, 'viewer-loading', '');
  const legendEl  = _createOverlay(container, 'viewer-legend', '');
  legendEl.style.cssText += 'bottom:8px;right:8px;top:auto;left:auto;max-width:180px;';
  loadingEl.style.display = 'none';
  legendEl.style.display  = 'none';

  // Grid placeholder (updated per representation)
  let gridHelper = null;

  // â”€â”€ Resize observer â”€â”€
  const resizeObs = new ResizeObserver(() => {
    if (disposed) return;
    renderer.setSize(container.clientWidth, container.clientHeight);
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
  });
  resizeObs.observe(container);

  // â”€â”€ Measurement event listeners â”€â”€
  renderer.domElement.addEventListener('pointerdown', e => { _measureStart = [e.clientX, e.clientY]; });
  let _measureStart = null;

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

  renderer.domElement.addEventListener('pointerup', e => {
    if (measureMode === 'orbit' || !_measureStart || Math.hypot(e.clientX - _measureStart[0], e.clientY - _measureStart[1]) > 5 || e.button !== 0) return;
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.set((e.clientX - rect.left) / rect.width * 2 - 1, -(e.clientY - rect.top) / rect.height * 2 + 1);
    ray.setFromCamera(mouse, camera);
    const targets = currentRepObject ? [currentRepObject] : [];
    const hit = ray.intersectObjects(targets, true)[0];
    if (!hit) return;
    measurePoints.push(hit.point.clone());
    _drawMeasure();
  });

  // Animation loop
  renderer.setAnimationLoop(() => { camController.update(); renderer.render(scene, camera); });

  // â”€â”€ Internal helpers â”€â”€

  function _createOverlay(parent, cls, html) {
    const el = document.createElement('div');
    el.className = cls;
    el.innerHTML = html;
    parent.style.position = 'relative';
    el.style.cssText = 'position:absolute;top:8px;left:8px;z-index:10;pointer-events:none;';
    parent.append(el);
    return el;
  }

  function setLoading(msg) {
    loadingEl.innerHTML = `<div class="viewer-loading-inner">${msg}</div>`;
    loadingEl.style.display = 'block';
  }
  function clearLoading() { loadingEl.style.display = 'none'; }

  function setLegend(html) {
    legendEl.innerHTML = html;
    legendEl.style.display = html ? 'block' : 'none';
  }
  function clearLegend() { legendEl.style.display = 'none'; legendEl.innerHTML = ''; }

  function disposeCurrentRepresentation() {
    if (currentRepObject) {
      scene.remove(currentRepObject);
      console.log("Traversing currentRepObject:", currentRepObject);
      currentRepObject.traverse(o => {
          console.log("Child:", o.type, o.isMesh, !!o.geometry, !!o.material);
        o.geometry?.dispose();
        if (o.material) {
          for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
            m.map?.dispose();
            m.dispose();
          }
        }
      });
      currentRepObject = null;
    }
    if (gridHelper) { scene.remove(gridHelper); gridHelper = null; }
    clearLegend();
    _clearMeasure();
  }

  function fitCamera(object) {
    const box = new THREE.Box3().setFromObject(object);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3()).length();
    cameraSize = size;
    controls.target.copy(center);
    camera.position.copy(center).add(new THREE.Vector3(size * 0.48, -size * 0.58, size * 0.5));
    camera.near = Math.max(size / 10000, 0.001);
    camera.far  = Math.max(size * 100, 100);
    camera.updateProjectionMatrix();
    controls.update();

    // Grid
    gridHelper = new THREE.GridHelper(size * 1.5, 20, 0x44603f, 0x263c2d);
    gridHelper.rotation.x = Math.PI / 2;
    gridHelper.position.set(center.x, center.y, box.min.z - size * 0.015);
    scene.add(gridHelper);
  }

  // â”€â”€ PLY loader â”€â”€
  async function _loadPLY(url, label, options = {}) {
    setLoading(`Loading ${label}â€¦`);
    const buf = await fetchBuf(url);
    const loader = new PLYLoader();
    const geometry = loader.parse(buf);
    geometry.computeBoundingBox();
    
    // Check if geometry has normals; compute if missing and we are rendering a mesh
    if (options.asMesh && !geometry.hasAttribute('normal')) {
      geometry.computeVertexNormals();
    }

    const hasCols = geometry.hasAttribute('color');
    let object, mat;

    if (options.asMesh) {
      // Determine if it actually contains face geometry
      // PLYLoader un-indexes geometry when face colors are present, so we check if position count > 0.
      // If the original PLY lacked faces entirely, three.js might just give us vertices.
      // However, we expect a mesh.
      mat = new THREE.MeshStandardMaterial({
        vertexColors: hasCols,
        color: hasCols ? 0xffffff : 0x9cac9c,
        roughness: 0.85,
        side: THREE.DoubleSide,
        flatShading: true,
      });
      object = new THREE.Mesh(geometry, mat);
    } else {
      mat = new THREE.PointsMaterial({
        size: 0.02,
        vertexColors: hasCols,
        color: hasCols ? 0xffffff : 0x88ccaa,
        sizeAttenuation: true,
      });
      object = new THREE.Points(geometry, mat);
    }

    clearLoading();
    return { object, mat };
  }

  // â”€â”€ GLB mesh loader â”€â”€
  async function _loadGLB(url) {
    setLoading('Loading meshâ€¦');
    const buf = await fetchBuf(url);
    const gltf = await new GLTFLoader().parseAsync(buf, '');
    clearLoading();
    return gltf.scene;
  }

  // â”€â”€ Representation loaders â”€â”€

  async function loadSparse(repsData) {
    if (!repsData.sparse?.available) throw new Error('Sparse cloud not available');
    const { object, mat } = await _loadPLY(repsData.sparse.url, 'Sparse Point Cloud', { asMesh: false });
    scene.add(object);
    currentRepObject = object; window.__viewer_debug_obj = object;
    fitCamera(object);
    _showPointSizeControl(mat, repsData.sparse.point_count);

    if (repsData.sparse.cameras_url) {
      try {
        const cbuf = await fetchBuf(repsData.sparse.cameras_url);
        const text = new TextDecoder().decode(cbuf);
        const { centers } = JSON.parse(text);
        if (centers && centers.length) {
          const pos = new Float32Array(centers.flat());
          const camGeo = new THREE.BufferGeometry();
          camGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
          const camPts = new THREE.Points(camGeo, new THREE.PointsMaterial({ color: 0xff6600, size: 0.04, sizeAttenuation: true }));
          
          const group = new THREE.Group();
          group.add(object);
          group.add(camPts);
          scene.remove(object);
          scene.add(group);
          currentRepObject = group;
          window.__viewer_debug_obj = object; // keep reference to actual sparse points for tests
        }
      } catch (_) { /* optional */ }
    }

    // Point size slider
    _showPointSizeControl(mat, repsData.sparse.point_count);

    setLegend(`<div class="legend-title">Sparse SfM</div>
      <div class="legend-item"><span class="legend-swatch" style="background:#88ccaa"></span>SfM Points</div>
      <div class="legend-item"><span class="legend-swatch" style="background:#ff6600"></span>Camera Centers</div>
      ${repsData.sparse.point_count ? `<div class="legend-count">${repsData.sparse.point_count.toLocaleString()} pts</div>` : ''}`);
  }

  async function loadDense(repsData) {
    if (!repsData.dense?.available) throw new Error('Dense point cloud not available');
    const label = repsData.dense.display_point_count
      ? `Dense Cloud (${repsData.dense.display_point_count.toLocaleString()} display pts)`
      : 'Dense Point Cloud';
    const { object, mat } = await _loadPLY(repsData.dense.url, label, { asMesh: false });
    scene.add(object);
    currentRepObject = object; window.__viewer_debug_obj = object;
    fitCamera(object);

    _showPointSizeControl(mat, repsData.dense.display_point_count);

    const note = repsData.dense.analysis_point_count && repsData.dense.display_point_count < repsData.dense.analysis_point_count
      ? `<div class="legend-note">Display: ${repsData.dense.display_point_count.toLocaleString()} / ${repsData.dense.analysis_point_count.toLocaleString()} pts (${repsData.dense.downsampling_method})</div>`
      : '';
    setLegend(`<div class="legend-title">Dense Cloud</div>${note}`);
  }

  async function loadMesh(repsData) {
    if (!repsData.mesh?.available) throw new Error('Mesh not available');
    setLoading('Loading geometry meshâ€¦');
    const model = await _loadGLB(repsData.mesh.url);
    // Replace all materials with neutral geometry-only material
    const geoMat = new THREE.MeshStandardMaterial({
      color: 0x9cac9c,
      metalness: 0,
      roughness: 0.85,
      side: THREE.DoubleSide,
    });
    model.traverse(o => {
      if (o.isMesh) {
        // Dispose original materials
        for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
          m.map?.dispose();
          m.dispose();
        }
        o.material = geoMat;
      }
    });
    scene.add(model);
    currentRepObject = model;
    fitCamera(model);
    clearLoading();
    setLegend(`<div class="legend-title">Geometry Mesh</div><div class="legend-note">Neutral shading Â· no texture</div>`);
  }

  async function loadTexturedMesh(repsData) {
    if (!repsData.textured?.available) throw new Error('Textured mesh not available');
    setLoading('Loading textured meshâ€¦');
    const model = await _loadGLB(repsData.textured.url);
    model.traverse(o => {
      if (o.isMesh) {
        if (Array.isArray(o.material)) {
          o.material.forEach(m => { m.side = THREE.DoubleSide; });
        } else {
          o.material.side = THREE.DoubleSide;
        }
      }
    });
    scene.add(model);
    currentRepObject = model;
    fitCamera(model);
    clearLoading();
    clearLegend();
  }

  async function loadSemantic(repsData) {
    if (!repsData.semantic?.available) throw new Error('Semantic model not available');
    const { object } = await _loadPLY(repsData.semantic.url, 'Semantic Model', { asMesh: true });
    // Override point material â€” colors embedded in PLY vertex colors
    if (object.material && !object.isMesh) {
      object.material.vertexColors = true;
      object.material.size = 0.015;
    }
    scene.add(object);
    currentRepObject = object; window.__viewer_debug_obj = object;
    fitCamera(object);

    // Build semantic legend
    const items = Object.entries(SEMANTIC_PALETTE)
      .map(([, v]) => `<div class="legend-item"><span class="legend-swatch" style="background:${v.color}"></span>${v.name}</div>`)
      .join('');
    setLegend(`<div class="legend-title">Semantic Classes</div>${items}`);
  }

  async function loadConfidence(repsData) {
    if (!repsData.confidence?.available) throw new Error('Confidence mesh not available');
    const { object } = await _loadPLY(repsData.confidence.url, 'Coverage/Confidence', { asMesh: true });
    if (object.material && !object.isMesh) {
      object.material.vertexColors = true;
      object.material.size = 0.015;
    }
    scene.add(object);
    currentRepObject = object; window.__viewer_debug_obj = object;
    fitCamera(object);

    const sup   = repsData.confidence.supported_face_ratio   != null ? (repsData.confidence.supported_face_ratio   * 100).toFixed(1) + '%' : 'â€”';
    const weak  = repsData.confidence.weak_face_ratio        != null ? (repsData.confidence.weak_face_ratio        * 100).toFixed(1) + '%' : 'â€”';
    const unobs = repsData.confidence.unobserved_face_ratio  != null ? (repsData.confidence.unobserved_face_ratio  * 100).toFixed(1) + '%' : 'â€”';

    const items = Object.entries(CONFIDENCE_PALETTE)
      .map(([k, v]) => `<div class="legend-item"><span class="legend-swatch" style="background:${v.color}"></span>${v.label}</div>`)
      .join('');

    setLegend(`<div class="legend-title">Coverage / Confidence</div>
      ${items}
      <div class="legend-note">Supported: ${sup}</div>
      <div class="legend-note">Weak: ${weak}</div>
      <div class="legend-note">Unobserved: ${unobs}</div>
      <div class="legend-note" style="color:#aaa;font-size:10px;">Support evidence, not accuracy</div>`);
  }

  // â”€â”€ Point size control â”€â”€
  let _pointSizeSlider = null;
  function _showPointSizeControl(mat, pointCount) {
    _removePointSizeControl();
    const ctrl = document.createElement('div');
    ctrl.className = 'point-size-control';
    ctrl.innerHTML = `<label>Point size<input type="range" min="1" max="30" value="10" step="1"></label>
      ${pointCount ? `<span>${pointCount.toLocaleString()} pts</span>` : ''}`;
    ctrl.querySelector('input').oninput = e => {
      mat.size = parseFloat(e.target.value) / 500;
    };
    container.append(ctrl);
    _pointSizeSlider = ctrl;
  }
  function _removePointSizeControl() {
    if (_pointSizeSlider) { _pointSizeSlider.remove(); _pointSizeSlider = null; }
  }

  // â”€â”€ Measurement helpers â”€â”€
  function _clearMeasure() {
    for (const o of [...annotations.children]) {
      annotations.remove(o);
      o.geometry?.dispose();
      o.material?.dispose();
    }
    measurePoints = [];
    measureFaces = [];
    measureMeshes = [];
    if (measureMode !== 'orbit') onMeasureUpdate(measureMode === 'surface_area' ? measureFaces : measurePoints, measureMode);
  }

  function _drawMeasure() {
    for (const o of measureMeshes) {
      annotations.remove(o);
      o.geometry?.dispose();
      o.material?.dispose();
    }
    measureMeshes = [];

    // Draw markers
    if (measureMode === 'surface_area') {
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
    }
  }

  window.getCurrentViewerType = () => { if (!currentRepObject) return 'None'; let type = currentRepObject.type; if (type === 'Group' || type === 'Scene') { currentRepObject.traverse(o => { if (o.isMesh) type = 'Mesh'; else if (o.isPoints && type !== 'Mesh') type = 'Points'; }); } return type; };
  
  // -- Fallback chain --
  const FALLBACK_ORDER = ['textured', 'mesh', 'dense', 'sparse'];

  async function loadWithFallback(preferredMode, repsData) {
    const order = preferredMode === 'textured' ? FALLBACK_ORDER :
                  preferredMode === 'mesh'     ? ['mesh', 'dense', 'sparse', 'textured'] :
                  [preferredMode, ...FALLBACK_ORDER.filter(m => m !== preferredMode)];

    const loaders = { sparse: loadSparse, dense: loadDense, mesh: loadMesh, textured: loadTexturedMesh, semantic: loadSemantic, confidence: loadConfidence };

    for (const mode of order) {
      if (!repsData[mode]?.available) continue;
      try {
        await loaders[mode](repsData);
        currentMode = mode;
        return mode;
      } catch (err) {
        console.warn(`Representation '${mode}' failed: ${err.message}`);
        disposeCurrentRepresentation();
        if (mode !== order[order.length - 1]) {
          setLoading(`${mode} failed. Trying next representation�`);
          await new Promise(r => setTimeout(r, 500));
        }
      }
    }
    throw new Error('No representation could be loaded');
  }

  // -- Public API --

  async function loadMode(mode) {
    if (disposed) return;
    _removePointSizeControl();
    disposeCurrentRepresentation();
    const loaders = { sparse: loadSparse, dense: loadDense, mesh: loadMesh, textured: loadTexturedMesh, semantic: loadSemantic, confidence: loadConfidence };
    const loader = loaders[mode];
    if (!loader) throw new Error(`Unknown mode: ${mode}`);
    if (!reps[mode]?.available) throw new Error(`Mode '${mode}' is not available`);
    try {
      await loader(reps);
      currentMode = mode;
    } catch (err) {
      if (mode === 'semantic' || mode === 'confidence') throw err;
      setLoading(`${mode} failed: ${err.message}. Trying fallback�`);
      await new Promise(r => setTimeout(r, 600));
      await loadWithFallback(mode, reps);
    }
  }

  function resetView() {
    if (currentRepObject) { fitCamera(currentRepObject); }
  }

  function wireframe(state) {
    if (!currentRepObject) return;
    currentRepObject.traverse(o => {
      if (o.isMesh && o.material) {
        const mats = Array.isArray(o.material) ? o.material : [o.material];
        mats.forEach(m => { m.wireframe = state !== undefined ? state : !m.wireframe; });
      }
    });
  }

  function setMode(v) {
    if (['ORBIT','FOCUS','WALK','FLY'].includes(v.toUpperCase())) { camController.setMode(v.toUpperCase()); measureMode = 'orbit'; _clearMeasure(); return; }
    camController.setMode('ORBIT');
    measureMode = v;
    _clearMeasure();
    measureLabel.textContent =
      v === 'orbit' ? 'Drag to explore' :
      v === 'area'  ? 'Select polygon corners in order on one plane' :
      'Select points to measure a path';
  }

  // HEATMAP INTEGRATION
      function applyHeatmapColors(colorsBuffer) { console.log("INSIDE applyHeatmapColors! currentRepObject is:", !!currentRepObject);
    if (!currentRepObject) return;
    let globalVertexOffset = 0;
    currentRepObject.traverse(o => {
      if (o.isMesh && o.geometry) { window.__viewer_debug_obj = o;
        if (!o.geometry.isNonIndexed && o.geometry.index) {
          o.geometry = o.geometry.toNonIndexed();
        }
        
        let numVerts = o.geometry.attributes.position.count;
        let numFloats = numVerts * 3;
        
        if (colorsBuffer) {
            if (globalVertexOffset * 3 + numFloats <= colorsBuffer.length) {
                let slice = colorsBuffer.subarray(globalVertexOffset * 3, globalVertexOffset * 3 + numFloats);
                o.geometry.setAttribute('heatmapColor', new THREE.BufferAttribute(slice, 3));
            } else {
                console.warn(`Face mapping mismatch! Vertices: ${numVerts}, Expected Floats: ${numFloats}, Remaining buffer: ${colorsBuffer.length - globalVertexOffset*3}`);
                const errColors = new Float32Array(numFloats);
                for(let i=0; i<errColors.length; i+=3) { errColors[i] = 1; errColors[i+2] = 1; }
                o.geometry.setAttribute('heatmapColor', new THREE.BufferAttribute(errColors, 3));
            }
            globalVertexOffset += numVerts;
        } else {
            if (o.geometry.attributes.heatmapColor) {
                o.geometry.deleteAttribute('heatmapColor');
            }
        }
        
        if (!o.material.isHeatmapPatched) {
          const originalOnBeforeCompile = o.material.onBeforeCompile;
          o.material.userData.heatmapOpacity = { value: 0.0 };
          o.material.onBeforeCompile = (shader) => {
            shader.uniforms.heatmapOpacity = o.material.userData.heatmapOpacity;
            
            shader.vertexShader = `
              #ifdef USE_HEATMAP
              attribute vec3 heatmapColor;
              varying vec3 vHeatmapColor;
              #endif
            ` + shader.vertexShader.replace(
              'void main() {',
              'void main() {\n#ifdef USE_HEATMAP\n  vHeatmapColor = heatmapColor;\n#endif'
            );
            
            shader.fragmentShader = `
              uniform float heatmapOpacity;
              #ifdef USE_HEATMAP
              varying vec3 vHeatmapColor;
              #endif
            ` + shader.fragmentShader.replace(
              '#include <dithering_fragment>',
              `#include <dithering_fragment>\n#ifdef USE_HEATMAP\ngl_FragColor = mix(vec4(0.0, 1.0, 1.0, 1.0), vec4(vHeatmapColor, gl_FragColor.a), heatmapOpacity);\n#endif`
            );
            
            if (originalOnBeforeCompile) originalOnBeforeCompile(shader);
          };
          
          o.material.customProgramCacheKey = function() {
              return 'heatmap_patched_v2';
          };
          o.material.defines = o.material.defines || {};
          o.material.defines.USE_HEATMAP = "";
          
          o.material.isHeatmapPatched = true;
          o.material.needsUpdate = true;
        }
      }
    });
  }

  // Initial load â€” fallback chain starting from textured
  await loadWithFallback('textured', reps);

  function setHeatmapOpacity(opacity) {
    if (!currentRepObject) return;
    currentRepObject.traverse(o => {
      if (o.isMesh && o.material && o.material.userData && o.material.userData.heatmapOpacity) {
        o.material.userData.heatmapOpacity.value = opacity;
      }
    });
  }
  function dispose() {
    disposed = true;
    if (renderer) renderer.dispose();
    if (controls) controls.dispose();
    if (camController) camController.dispose();
  }
  return { loadMode, setMode, clear: _clearMeasure, wireframe, resetView, applyHeatmapColors, setHeatmapOpacity, dispose };
}






