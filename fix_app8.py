from pathlib import Path

p = Path("web/app.js")
js = p.read_text(encoding="utf-8")

# Let's restore from git first to get a clean slate
import subprocess

subprocess.run(["git", "restore", "web/app.js"])
js = p.read_text(encoding="utf-8")

# 1. Add import
js = "import * as Meas from './measurements.js';\n" + js

# 2. Replace tab-viewer UI
start = js.find('<div class="tab-content" id="tab-viewer">')
end = js.find('<div class="tab-content" id="tab-map">')

new_tab_viewer = """    <div class="tab-content" id="tab-viewer">
      <div class="viewer-selector" style="margin-bottom: 10px;">
        <select id="representation-selector"></select>
        <button id="reset-view" style="margin-left:8px;">Reset View</button>
        <button id="wireframe-btn" style="margin-left:4px;">Wireframe</button>
      </div>
      <div class="viewer" id="viewer">
        <div class="viewer-label">${metric ? 'METRIC ALIGNMENT' : 'RELATIVE COORDINATES'}<br>Drag to orbit · right drag to pan · scroll to zoom</div>
      </div>
      <div class="viewer-tools" style="display: flex; gap: 5px; flex-wrap: wrap;">
        <button data-mode="orbit" class="active">Orbit</button>
        <button data-mode="distance">Distance</button>
        <button data-mode="area">Area</button>
        <button data-mode="slope">Slope</button>
        <button data-mode="angle">Angle</button>
        <button id="clear-measure" style="background-color: #552222; color: #ffaaaa; margin-left: auto;">Clear Current</button>
        <button id="clear-all-measure" style="background-color: #552222; color: #ffaaaa;">Clear All</button>
      </div>
      <div id="measure-result" style="background: rgba(0,0,0,0.5); padding: 10px; margin-top: 10px; border-radius: 4px; font-family: monospace; min-height: 40px; font-size: 13px;">
        Select a tool to begin measuring.
      </div>
      <div id="measure-history" style="margin-top: 10px; max-height: 150px; overflow-y: auto; font-size: 13px;">
      </div>
      <div class="notice" id="measure-notice"></div>
    </div>
"""
js = js[:start] + new_tab_viewer + "\n  " + js[end:]

# 3. Fix createViewer call to include onMeasureUpdate callback
old_createViewer = """    viewer = await createViewer(
      viewerContainer,
      j.id,
      reps || { textured: { available: true, url: `/api/jobs/${j.id}/files/mesh/model.glb` } },
      metric
    );"""

new_createViewer = """    viewer = await createViewer(
      viewerContainer,
      j.id,
      reps || { textured: { available: true, url: `/api/jobs/${j.id}/files/mesh/model.glb` } },
      metric,
      {
         onMeasureUpdate: (pts, mode) => {
             if (window._handleMeasureUpdate) window._handleMeasureUpdate(pts, mode);
         }
      }
    );"""

js = js.replace(old_createViewer, new_createViewer)

# 4. Replace Measurement tools events
old_events = """      // Measurement tools
      document.querySelectorAll('[data-mode]').forEach(b => b.onclick = () => {
        if (b.disabled) return;
        document.querySelectorAll('[data-mode]').forEach(x => x.classList.toggle('active', x === b));
        viewer.setMode(b.dataset.mode);
      });
      $('#clear-measure').onclick = () => viewer.clear();"""

new_events = """      // Measurement state
      let measureHistory = [];
      let measureCount = 0;
      
      const caps = Meas.getMeasurementCapabilities(r.metric_state);
      
      // Update buttons availability
      document.querySelectorAll('[data-mode]').forEach(b => {
          const mode = b.dataset.mode;
          if (!caps.metric_distance && (mode !== 'orbit')) {
              b.title = "Model units only";
          }
      });
      
      // Hook up UI
      const resultPanel = $('#measure-result');
      const historyPanel = $('#measure-history');
      
      function updateHistoryUI() {
          historyPanel.innerHTML = measureHistory.map(m => `
              <div style="border-bottom: 1px solid #333; padding: 5px 0;">
                <strong>${m.id}</strong> (${m.mode}): ${m.summary}
              </div>
          `).reverse().join('');
      }

      function handleMeasureUpdate(points, mode) {
          if (mode === 'orbit' || points.length === 0) {
              resultPanel.innerHTML = "Select points to measure.";
              return;
          }
          
          let resultHtml = `<strong>Current (${mode})</strong> - ${points.length} pts selected<br>`;
          let summary = "";
          let complete = false;
          
          if (mode === 'distance') {
              if (points.length >= 2) {
                  const a = points[points.length-2];
                  const b = points[points.length-1];
                  const d3 = Meas.distance3D(a, b);
                  const dh = Meas.horizontalDistance(a, b);
                  const dv = Meas.verticalDifference(a, b);
                  const dxyz = Meas.deltaXYZ(a, b);
                  
                  resultHtml += `Segment 3D: ${Meas.formatNumber(d3)} ${caps.unit}<br>`;
                  resultHtml += `Segment Horiz: ${Meas.formatNumber(dh)} ${caps.unit}<br>`;
                  resultHtml += `Segment Vert: ${Meas.formatNumber(dv)} ${caps.unit}<br>`;
                  resultHtml += `ΔX: ${Meas.formatNumber(dxyz.x)}, ΔY: ${Meas.formatNumber(dxyz.y)}, ΔZ: ${Meas.formatNumber(dxyz.z)}<br>`;
                  
                  let totalD = 0;
                  for (let i=1; i<points.length; i++) totalD += Meas.distance3D(points[i-1], points[i]);
                  resultHtml += `<br><strong>Total Path 3D: ${Meas.formatNumber(totalD)} ${caps.unit}</strong>`;
                  summary = `Path ${Meas.formatNumber(totalD)} ${caps.unit}`;
              }
          } else if (mode === 'area') {
              if (points.length >= 3) {
                  const a = Meas.planarArea3D(points);
                  resultHtml += `<strong>Planar Area: ${Meas.formatNumber(a)} ${caps.area_unit}</strong>`;
                  summary = `Area ${Meas.formatNumber(a)} ${caps.area_unit}`;
              } else {
                  resultHtml += `Select at least 3 points.`;
              }
          } else if (mode === 'slope') {
              if (points.length >= 2) {
                  const sl = Meas.slope(points[0], points[1]);
                  resultHtml += `Horiz: ${Meas.formatNumber(sl.horizontal)} ${caps.unit}, Vert: ${Meas.formatNumber(sl.vertical)} ${caps.unit}<br>`;
                  resultHtml += `<strong>Slope: ${Meas.formatNumber(sl.degrees)}°</strong> (Grade: ${Meas.formatNumber(sl.percentage)}%)`;
                  summary = `Slope ${Meas.formatNumber(sl.degrees)}°`;
                  complete = true;
              } else {
                  resultHtml += `Select 2 points.`;
              }
          } else if (mode === 'angle') {
              if (points.length >= 3) {
                  const ang = Meas.angle3(points[0], points[1], points[2]);
                  resultHtml += `<strong>Angle at P2: ${Meas.formatNumber(ang)}°</strong>`;
                  summary = `Angle ${Meas.formatNumber(ang)}°`;
                  complete = true;
              } else {
                  resultHtml += `Select 3 points (angle at P2).`;
              }
          }
          
          if (points.length > 0) {
              const last = points[points.length-1];
              resultHtml += `<br><span style="color:#888;">Last point: (${Meas.formatNumber(last.x)}, ${Meas.formatNumber(last.y)}, ${Meas.formatNumber(last.z)})</span>`;
          }
          
          if (!caps.metric_distance) {
              resultHtml += `<br><span style="color:#ff8888;">Warning: Model units only. Metric alignment unavailable.</span>`;
          }
          
          resultPanel.innerHTML = resultHtml;
          
          if (complete) {
              measureCount++;
              measureHistory.push({ id: 'M' + measureCount, mode, summary, points: [...points] });
              updateHistoryUI();
              viewer.clear(); // auto restart
          }
      }

      window._handleMeasureUpdate = handleMeasureUpdate;

      document.querySelectorAll('[data-mode]').forEach(b => b.onclick = () => {
        if (b.disabled) return;
        document.querySelectorAll('[data-mode]').forEach(x => x.classList.toggle('active', x === b));
        viewer.setMode(b.dataset.mode);
        resultPanel.innerHTML = "Select points on the model.";
      });
      $('#clear-measure').onclick = () => {
         viewer.clear();
         resultPanel.innerHTML = "Cleared.";
      };
      $('#clear-all-measure').onclick = () => {
         viewer.clear();
         measureHistory = [];
         measureCount = 0;
         updateHistoryUI();
         resultPanel.innerHTML = "All measurements cleared.";
      };
      
      // Allow ending distance/area with right-click
      viewerContainer.oncontextmenu = (e) => {
         e.preventDefault();
         const activeBtn = document.querySelector('[data-mode].active');
         if (activeBtn) {
             const mode = activeBtn.dataset.mode;
             if (mode === 'distance' || mode === 'area') {
                 const html = resultPanel.innerHTML;
                 let summary = "Finished";
                 if (html.includes("Total Path 3D:")) summary = html.split("Total Path 3D:")[1].split("</strong>")[0].replace(/<[^>]+>/g, '').trim();
                 else if (html.includes("Planar Area:")) summary = html.split("Planar Area:")[1].split("</strong>")[0].replace(/<[^>]+>/g, '').trim();
                 
                 measureCount++;
                 measureHistory.push({ id: 'M' + measureCount, mode, summary });
                 updateHistoryUI();
                 viewer.clear();
             }
         }
      };"""

js = js.replace(old_events, new_events)

p.write_text(js, encoding="utf-8")
