from pathlib import Path

p = Path("web/app.js")
js = p.read_text(encoding="utf-8")

# 1. Add import at the top
if "import * as Meas" not in js:
    js = "import * as Meas from './measurements.js';\n" + js

# 2. Add Measurement UI logic replacing the old measurement tools events

old_events = '''      // Measurement tools
      document.querySelectorAll('[data-mode]').forEach(b => b.onclick = () => {
        if (b.disabled) return;
        document.querySelectorAll('[data-mode]').forEach(x => x.classList.toggle('active', x === b));
        viewer.setMode(b.dataset.mode);
      });
      #clear-measure.onclick = () => viewer.clear();'''

new_events = '''
      // Measurement state
      let measureHistory = [];
      let measureCount = 0;
      
      const caps = Meas.getMeasurementCapabilities(r.metric_state);
      
      // Update buttons availability
      document.querySelectorAll('[data-mode]').forEach(b => {
          const mode = b.dataset.mode;
          if (!caps.metric_distance && (mode !== 'orbit')) {
              // We allow geometric tools even if relative, they just show model units
              // Wait, relative doesn't disable geometric tools, it just uses model units!
          }
      });
      
      // Hook up UI
      const resultPanel = #measure-result;
      const historyPanel = #measure-history;
      
      function updateHistoryUI() {
          historyPanel.innerHTML = measureHistory.map(m => 
              <div style="border-bottom: 1px solid #333; padding: 5px 0;">
                <strong>\\</strong> (\\): \
              </div>
          ).reverse().join('');
      }

      function handleMeasureUpdate(points, mode) {
          if (mode === 'orbit' || points.length === 0) {
              resultPanel.innerHTML = "Select points to measure.";
              return;
          }
          
          let resultHtml = <strong>Current (\\)</strong> - \\ pts selected<br>;
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
                  
                  resultHtml += Segment 3D: \\ \\<br>;
                  resultHtml += Segment Horiz: \\ \\<br>;
                  resultHtml += Segment Vert: \\ \\<br>;
                  resultHtml += ΔX: \\, ΔY: \\, ΔZ: \\<br>;
                  
                  let totalD = 0;
                  for (let i=1; i<points.length; i++) totalD += Meas.distance3D(points[i-1], points[i]);
                  resultHtml += <br><strong>Total Path 3D: \\ \\</strong>;
                  summary = Path \\ \\;
              }
          } else if (mode === 'area') {
              if (points.length >= 3) {
                  const a = Meas.planarArea3D(points);
                  resultHtml += <strong>Planar Area: \\ \\</strong>;
                  summary = Area \\ \\;
              } else {
                  resultHtml += Select at least 3 points.;
              }
          } else if (mode === 'slope') {
              if (points.length >= 2) {
                  const sl = Meas.slope(points[0], points[1]);
                  resultHtml += Horiz: \\ \\, Vert: \\ \\<br>;
                  resultHtml += <strong>Slope: \\°</strong> (Grade: \\%);
                  summary = Slope \\°;
                  complete = true;
              } else {
                  resultHtml += Select 2 points.;
              }
          } else if (mode === 'angle') {
              if (points.length >= 3) {
                  const ang = Meas.angle3(points[0], points[1], points[2]);
                  resultHtml += <strong>Angle at P2: \\°</strong>;
                  summary = Angle \\°;
                  complete = true;
              } else {
                  resultHtml += Select 3 points (angle at P2).;
              }
          }
          
          if (points.length > 0) {
              const last = points[points.length-1];
              resultHtml += <br><span style="color:#888;">Last point: (\\, \\, \\)</span>;
          }
          
          if (!caps.metric_distance) {
              resultHtml += <br><span style="color:#ff8888;">Warning: Model units only. Metric alignment unavailable.</span>;
          }
          
          resultPanel.innerHTML = resultHtml;
          
          if (complete) {
              measureCount++;
              measureHistory.push({ id: 'M' + measureCount, mode, summary, points: [...points] });
              updateHistoryUI();
              viewer.clear(); // auto restart
          }
      }

      // We need to pass the callback into createViewer options!
      // But we already called createViewer above...
'''

# We need to add onMeasureUpdate: handleMeasureUpdate to the options passed to createViewer.
old_createViewer = '''    viewer = await createViewer(
      viewerContainer,
      j.id,
      reps || { textured: { available: true, url: /api/jobs//files/mesh/model.glb } },
      metric
    );'''

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

new_events_2 = '''
      // Hook the global variable so createViewer callback sees it
      window._handleMeasureUpdate = handleMeasureUpdate;

      document.querySelectorAll('[data-mode]').forEach(b => b.onclick = () => {
        if (b.disabled) return;
        document.querySelectorAll('[data-mode]').forEach(x => x.classList.toggle('active', x === b));
        viewer.setMode(b.dataset.mode);
        resultPanel.innerHTML = "Select points on the model.";
      });
      #clear-measure.onclick = () => {
         viewer.clear();
         resultPanel.innerHTML = "Cleared.";
      };
      #clear-all-measure.onclick = () => {
         viewer.clear();
         measureHistory = [];
         measureCount = 0;
         updateHistoryUI();
         resultPanel.innerHTML = "All measurements cleared.";
      };
      
      // Allow ending distance/area with right-click?
      viewerContainer.oncontextmenu = (e) => {
         e.preventDefault();
         const activeBtn = document.querySelector('[data-mode].active');
         if (activeBtn) {
             const mode = activeBtn.dataset.mode;
             if (mode === 'distance' || mode === 'area') {
                 // finish current
                 // we grab current text from resultPanel to get summary, or just trigger a dummy clear
                 const html = resultPanel.innerHTML;
                 let summary = "Finished";
                 if (html.includes("Total Path 3D:")) summary = html.split("Total Path 3D:")[1].split("</strong>")[0].replace(/<[^>]+>/g, '').trim();
                 if (html.includes("Planar Area:")) summary = html.split("Planar Area:")[1].split("</strong>")[0].replace(/<[^>]+>/g, '').trim();
                 
                 measureCount++;
                 measureHistory.push({ id: 'M' + measureCount, mode, summary });
                 updateHistoryUI();
                 viewer.clear();
             }
         }
      };
'''

js = js.replace(old_createViewer, new_createViewer)
js = js.replace(old_events, new_events + new_events_2)

p.write_text(js, encoding="utf-8")
