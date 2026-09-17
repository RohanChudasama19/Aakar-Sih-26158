import * as Meas from './measurements.js';
const $=s=>document.querySelector(s);
let token=sessionStorage.getItem('aerorecon-token')||'', activeJob=null, streamAbort=null, viewer=null, renderedJob=null;
const headers=()=>token?{Authorization:`Bearer ${token}`} : {};
async function api(path,opts={}){const r=await fetch(path,{...opts,headers:{...headers(),...opts.headers}});if(!r.ok){const e=await r.json().catch(()=>({detail:r.statusText}));throw Error(typeof e.detail==='string'?e.detail:JSON.stringify(e.detail));}return r;}
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function toast(s){$('#toast').textContent=s;$('#toast').hidden=false;setTimeout(()=>$('#toast').hidden=true,5000);}
function newMission(){ $('#upload-error').textContent='';$('#submit-dialog').showModal(); }
['#new-mission','#empty-new','#nav-new'].forEach(x=>$(x).onclick=newMission);
$('#close-submit').onclick=()=>$('#submit-dialog').close();
['#nav-guide','#sample-guide','#quality-guide'].forEach(x=>$(x).onclick=e=>{e.preventDefault();$('#guide-dialog').showModal();});
$('#close-guide').onclick=()=>$('#guide-dialog').close();
$('#auth-button').onclick=()=>{const value=prompt('API access token (leave empty for local mode)',token);if(value!==null){token=value;sessionStorage.setItem('aerorecon-token',token);refresh();}};
$('#video-file').onchange=e=>$('#video-name').textContent=e.target.files[0]?.name||'Choose video file';
$('#nav-missions').onclick=closeDetail;$('#refresh').onclick=refresh;
async function refresh(){try{const [health,jobs]=await Promise.all([(await api('/api/health')).json(),(await api('/api/jobs')).json()]);$('#worker-message').textContent=health.queue.message;$('#worker-short').textContent=health.queue.available?'Worker connected':'Worker offline';$('#count-total').textContent=jobs.length;$('#job-count').textContent=jobs.length;$('#list-count').textContent=String(jobs.length).padStart(2,'0');$('#count-done').textContent=jobs.filter(j=>j.status==='completed').length;$('#count-running').textContent=jobs.filter(j=>['running','queued'].includes(j.status)).length;$('#empty').hidden=!!jobs.length;$('#missions').innerHTML=jobs.map(j=>`<button class="mission-card" data-id="${j.id}"><div class="card-scene">${j.status==='completed'?'◈':'⌁'}</div><div class="card-body"><h3>${esc(j.name)}</h3><span class="status ${j.status}">${esc(j.status)}</span><p>${new Date(j.created*1000).toLocaleString()} · ${esc(j.options.engine.toUpperCase())}</p><progress max="100" value="${j.progress}"></progress></div></button>`).join('');document.querySelectorAll('.mission-card').forEach(e=>e.onclick=()=>openJob(e.dataset.id));}catch(e){$('#worker-message').textContent=e.message;$('#worker-short').textContent='Connection unavailable';}}
$('#load-sample').onclick=async()=>{const b=$('#load-sample');b.disabled=true;try{for(const [field,name,type]of[['video','sample.mp4','video/mp4'],['gps','gps.csv','text/csv'],['flight','flight.json','application/json']]){const blob=await(await api('/api/samples/'+name)).blob();const transfer=new DataTransfer();transfer.items.add(new File([blob],name,{type}));$(`[name=${field}]`).files=transfer.files;}$('[name=name]').value='Synthetic campus · smoke test';$('[name=engine]').value='cpu';$('[name=max_frames]').value='60';$('#video-name').textContent='sample.mp4 · synthetic test scene';toast('Sample files loaded. Click Start reconstruction.');}catch(e){$('#upload-error').textContent=e.message;}finally{b.disabled=false;}};
$('#upload-form').onsubmit=e=>{e.preventDefault();const button=$('#submit-button');button.disabled=true;$('#upload-error').textContent='';$('#upload-progress').hidden=false;const form=new FormData(e.target);for(const [k,v]of [...form.entries()])if(v instanceof File&&!v.size)form.delete(k);const xhr=new XMLHttpRequest();xhr.open('POST','/api/jobs');if(token)xhr.setRequestHeader('Authorization',`Bearer ${token}`);xhr.upload.onprogress=e=>{const n=e.lengthComputable?100*e.loaded/e.total:0;$('#upload-progress progress').value=n;$('#upload-progress span').textContent=n<100?`Uploading ${Math.round(n)}% · ${(e.loaded/1048576).toFixed(1)} MB transferred`:'Upload transferred · validating inputs and queuing job…';};xhr.onerror=()=>{button.disabled=false;$('#upload-error').textContent='Upload connection failed. Check the server and retry.';};xhr.onload=()=>{button.disabled=false;let data;try{data=JSON.parse(xhr.responseText);}catch{data={detail:'Server returned an unexpected response'};}if(xhr.status>=200&&xhr.status<300){$('#submit-dialog').close();$('#upload-progress').hidden=true;refresh();openJob(data.id);}else{$('#upload-error').textContent=typeof data.detail==='string'?data.detail:JSON.stringify(data.detail);}};xhr.send(form);};
const stageNames=['Ingest & prepare','Camera poses','Dense geometry','Mesh & texture','Georeference','Scene report'];
function closeDetail(){activeJob=null;streamAbort?.abort();viewer?.dispose();viewer=null;renderedJob=null;$('#detail').hidden=true;refresh();}
async function openJob(id){streamAbort?.abort();viewer?.dispose();viewer=null;renderedJob=null;activeJob=id;$('#detail').hidden=false;$('#detail').innerHTML=`<div class="detail-heading"><div><div class="eyebrow">MISSION WORKSPACE</div><h2 id="detail-name">Loading mission…</h2></div><div class="action-row"><button class="text-button" id="btn-cancel" hidden>Cancel</button><button class="text-button" id="btn-retry" hidden>Retry</button><button class="text-button" id="back">← All missions</button></div></div><div class="system-bar" id="job-message"></div><div class="stage-list">${stageNames.map((s,i)=>`<div class="stage-item" data-stage="${String.fromCharCode(65+i)}"><b>${String.fromCharCode(65+i)}</b>${s}</div>`).join('')}</div><progress id="job-progress" max="100" value="0"></progress><div id="results"></div>`;$('#back').onclick=closeDetail;try{const j=await(await api('/api/jobs/'+id)).json();await updateDetail(j);if(!['failed','completed','cancelled','RECONSTRUCTION_BLOCKED'].includes(j.status))watch(id);}catch(e){$('#job-message').textContent=e.message;}}
async function watch(id){streamAbort=new AbortController();try{const r=await api(`/api/jobs/${id}/events`,{signal:streamAbort.signal});const reader=r.body.getReader(),decoder=new TextDecoder();let pending='';while(true){const {value,done}=await reader.read();if(done)break;pending+=decoder.decode(value,{stream:true});let n;while((n=pending.indexOf('\n\n'))>=0){const block=pending.slice(0,n);pending=pending.slice(n+2);if(block.startsWith('data: '))await updateDetail(JSON.parse(block.slice(6)));}}}catch(e){if(e.name!=='AbortError'&&activeJob===id){$('#job-message').textContent='Live connection interrupted. Reconnecting…';setTimeout(()=>activeJob===id&&watch(id),3000);}}}
async function updateDetail(j){if(activeJob!==j.id)return;$('#detail-name').textContent=j.name;$('#job-message').textContent=j.message;$('#job-progress').value=j.progress;document.querySelectorAll('.stage-item').forEach(e=>{e.className='stage-item';if(j.status==='completed'||e.dataset.stage<j.stage)e.classList.add('done');else if(e.dataset.stage===j.stage)e.classList.add('running');});$('#btn-cancel').hidden = ['completed','failed','cancelled','RECONSTRUCTION_BLOCKED'].includes(j.status);$('#btn-cancel').onclick = async () => { $('#btn-cancel').disabled=true; await api('/api/jobs/'+j.id+'/cancel', {method:'POST'}); refresh(); };$('#btn-retry').hidden = !['completed','failed','cancelled','RECONSTRUCTION_BLOCKED'].includes(j.status);$('#btn-retry').onclick = async () => { $('#btn-retry').disabled=true; await api('/api/jobs/'+j.id+'/retry', {method:'POST'}); closeDetail(); openJob(j.id); };if(j.status==='cancelled'){$('#results').innerHTML='<div class="notice error">Job cancelled.</div>';return;}if(j.status==='RECONSTRUCTION_BLOCKED'){$('#results').innerHTML='<div class="notice" style="background:#fff3cd; color:#856404;"><h3>Reconstruction Blocked</h3><p><strong>Reason:</strong> '+esc(j.message)+'</p>'+(j.report&&j.report.readiness?'<h4>Readiness Metrics:</h4><pre>'+esc(JSON.stringify(j.report.readiness,null,2))+'</pre>':'')+'<p><strong>Recommendations:</strong> Ensure sharp frames, adequate overlap, and GPS telemetry before retrying.</p></div>';return;}if(j.status==='failed'){$('#results').innerHTML='<div class="notice error">Reconstruction stopped. '+esc(j.message)+'<br>Check the capture guide and worker logs before retrying.</div>';return;}if(j.status==='completed'&&renderedJob!==j.id){renderedJob=j.id;await showResults(j);}}
async function download(url,name){try{if(!token){const a=document.createElement('a');a.href=url;a.download=name;a.click();return;}const blob=await(await api(url)).blob();const object=URL.createObjectURL(blob);const a=document.createElement('a');a.href=object;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(object),10000);}catch(e){toast(e.message);}}

// ── Mode display names ──
const MODE_LABELS = {
  textured:   'Textured Mesh',
  mesh:       'Mesh (Geometry)',
  dense:      'Dense Point Cloud',
  sparse:     'Sparse Point Cloud',
  semantic:   'Semantic',
  confidence: 'Confidence / Coverage',
};
const MODE_ORDER = ['textured','mesh','dense','sparse','semantic','confidence'];

async function showResults(j) {
  const r = j.report;
  const metric = r.metric_state === 'GEOREFERENCED_METRIC' || r.metric_state === 'GPS_ALIGNED_UNVERIFIED' || r.metric_state === 'METRIC_SCALE';

  // Fetch deliverables matrix
  let matrixHTML = '';
  try {
    const matrixReq = await api(`/api/jobs/${j.id}/files/reports/deliverables_matrix.json`);
    if (matrixReq.ok) {
      const matrix = await matrixReq.json();
      matrixHTML = `<div class="deliverables-grid">
        <div class="del-row header"><div class="del-col">Format</div><div class="del-col">Purpose</div><div class="del-col">Verified</div></div>
        ${matrix.map(m => `<div class="del-row"><div class="del-col"><strong>${m.Format}</strong></div><div class="del-col">${m.Purpose}</div><div class="del-col">${m.Verified ? '✅ Yes' : '❌ No'}</div></div>`).join('')}
      </div>`;
    }
  } catch (_) {
    matrixHTML = '<p>Deliverables matrix unavailable.</p>';
  }

  // Fetch representations manifest for viewer
  let reps = null;
  try {
    reps = await (await api(`/api/jobs/${j.id}/representations`)).json();
  } catch (_) { /* viewer falls back to trying GLB directly */ }

  $('#results').innerHTML = `
    <div class="tabs-header">
      <button class="tab-btn active" data-tab="overview">Overview</button>
      <button class="tab-btn" data-tab="viewer">3D Viewer</button>
      <button class="tab-btn" data-tab="map">Map</button>
      <button class="tab-btn" data-tab="measurements">Measurements</button>
      <button class="tab-btn" data-tab="analysis">Analysis</button>
      <button class="tab-btn" data-tab="validation">Validation</button>
      <button class="tab-btn" data-tab="exports">Exports</button>
      <button class="tab-btn" data-tab="technical">Technical</button>
    </div>

    <div class="tab-content active" id="tab-overview">
      <div class="notice">Surface: ${esc(r.mesh.surface_quality || 'QUALITY NOT ASSESSED')}. ${esc(r.mesh.note || '')}</div>
      <div class="result-metrics">
        <div><span>PROCESSING TIME</span><strong>${r.processing_time_sec.toFixed(1)} s</strong><small>${r.video_duration_sec.toFixed(1)}s video</small></div>
        <div><span>REGISTERED CAMERAS</span><strong>${r.targets.coverage.registered_frames} / ${r.targets.coverage.selected_frames}</strong></div>
        <div><span>METRIC STATE</span><strong>${esc(r.metric_state)}</strong></div>
      </div>
      <div class="export-list" style="margin-top: 20px;">
        <button id="download-all">↓ Download Deliverables ZIP</button>
        <button id="download-report">↓ Mission Report</button>
      </div>
    </div>

        <div class="tab-content" id="tab-viewer">
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
        <button data-mode="area">Planar Area</button>
        <button data-mode="surface_area">Surface Area</button>
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

  <div class="tab-content" id="tab-map">
      <div id="map-notice" class="notice" style="display:none;"></div>
      <div id="map-container" style="display:none;">
        <div class="result-metrics" id="map-metrics" style="margin-bottom: 10px;"></div>
        <div id="leaflet-map" style="height: 600px; width: 100%; border-radius: 6px;"></div>
        <div class="notice" style="margin-top: 10px; padding: 10px; background: rgba(0,0,0,0.4);">
           <span style="display:inline-block; width:12px; height:12px; background:#ff4444; border-radius:50%; margin-right:5px; vertical-align:middle;"></span> GPS Trajectory
           <span style="display:inline-block; width:12px; height:12px; background:#4444ff; border-radius:50%; margin-right:5px; margin-left:15px; vertical-align:middle;"></span> Reconstructed Camera Trajectory
           <span style="display:inline-block; margin-left: 20px;" id="map-coords"></span>
        </div>
      </div>
    </div>
    </div>

    <div class="tab-content" id="tab-measurements">
      <p>Measurements can be performed in the <strong>3D Viewer</strong> tab.</p>
    </div>

    <div class="tab-content" id="tab-analysis">
      <h3>Semantic Regions</h3>
      <p>Semantic modeling extracts rough structural candidates.</p>
      <pre>${esc(JSON.stringify(r.semantics || {}, null, 2))}</pre>
    </div>

    <div class="tab-content" id="tab-validation">
        <div class="validation-panel">
          <h3>Alignment Quality</h3>
          <p><strong>GPS Alignment Residual (RMSE):</strong>
            \</p>
          <p><strong>Inliers / Samples:</strong>
            \</p>
          <p><strong>Metric State:</strong> \</p>
          <p style="font-size:11px;color:#888;font-style:italic;">
            This is a Sim(3) fit residual — it measures how well camera positions match the
            GPS trajectory used to estimate the georeferencing transform.
            It is NOT independent spatial accuracy.
          </p>
        </div>
        <hr style="border-color:#333;margin:16px 0;">
        <div class="validation-panel" id="indep-validation-panel">
          <h3>Independent Spatial Validation</h3>
          <p id="indep-validation-status"><em>Loading...</em></p>
          <div id="indep-validation-detail" style="display:none">
            <table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:8px;">
              <tbody>
                <tr><th style="text-align:left;padding:4px 8px;color:#aaa;">Horizontal RMSE</th><td id="vi-rmse-h" style="padding:4px 8px;">-</td></tr>
                <tr><th style="text-align:left;padding:4px 8px;color:#aaa;">Vertical RMSE</th><td id="vi-rmse-z" style="padding:4px 8px;">-</td></tr>
                <tr><th style="text-align:left;padding:4px 8px;color:#aaa;">3D RMSE</th><td id="vi-rmse-3d" style="padding:4px 8px;">-</td></tr>
                <tr><th style="text-align:left;padding:4px 8px;color:#aaa;">Mean 3D error</th><td id="vi-mean" style="padding:4px 8px;">-</td></tr>
                <tr><th style="text-align:left;padding:4px 8px;color:#aaa;">Checkpoints used</th><td id="vi-count" style="padding:4px 8px;">-</td></tr>
                <tr><th style="text-align:left;padding:4px 8px;color:#aaa;">Threshold (SIH)</th><td id="vi-thresh" style="padding:4px 8px;">-</td></tr>
                <tr><th style="text-align:left;padding:4px 8px;color:#aaa;">Pass rule</th><td id="vi-rule" style="padding:4px 8px;">-</td></tr>
              </tbody>
            </table>
            <div id="vi-warnings" style="color:#c88;margin-top:8px;font-size:11px;"></div>
            <div id="vi-cptable-wrap" style="margin-top:12px;overflow-x:auto;font-size:12px;"></div>
          </div>
          <div style="margin-top:18px;padding:12px;border:1px solid #333;border-radius:6px;background:#141f16;">
            <p style="margin:0 0 8px;font-size:13px;font-weight:600;">Upload Independent Checkpoints CSV</p>
            <p style="margin:0 0 8px;font-size:11px;color:#8a8;">
              Used <strong>only for validation</strong>. Not used to fit the georeferencing transform.
            </p>
            <input type="file" id="checkpoint-upload-input" accept=".csv" style="font-size:12px;">
            <button id="checkpoint-upload-btn" style="margin-left:8px;font-size:12px;">Upload</button>
            <p id="checkpoint-upload-msg" style="font-size:11px;color:#aaa;margin-top:6px;"></p>
          </div>
        </div>
      </div>

    <div class="tab-content" id="tab-exports">
      <h3>Export Center</h3>
      ${matrixHTML}
    </div>

    <div class="tab-content" id="tab-technical">
      <h3>Technical Pipeline Report</h3>
      <ul class="warnings" style="margin-bottom: 20px;">${r.warnings.map(w => `<li>${esc(w)}</li>`).join('')}</ul>
      <pre>${esc(JSON.stringify(r, null, 2))}</pre>
    </div>
  `;

  // Tab switching
  let leafletMap = null;
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
      
      if (btn.dataset.tab === 'map') {
         if (!window.leafletMap) {
            initMap(j.id);
         } else {
            window.leafletMap.invalidateSize();
         }
      }
    };
  });

  

  $('#download-all').onclick = () => download(`/api/jobs/${j.id}/download`, `mission_${j.id}_deliverables.zip`);
  $('#download-report').onclick = () => download(`/api/jobs/${j.id}/files/reports/mission_report.json`, 'mission_report.json');

  // ── Build representation selector from API ──
  const sel = $('#representation-selector');
  if (reps) {
    MODE_ORDER.forEach(mode => {
      const rep = reps[mode];
      const opt = document.createElement('option');
      opt.value = mode;
      const avail = rep?.available;
      opt.textContent = avail ? MODE_LABELS[mode] : `${MODE_LABELS[mode]} [Unavailable]`;
      opt.disabled = !avail;
      // Select first available as default
      sel.append(opt);
    });
    // Set to first available
    const firstAvail = MODE_ORDER.find(m => reps[m]?.available);
    if (firstAvail) sel.value = firstAvail;
  } else {
    // Fallback: just show GLB modes if no representations API
    ['textured','mesh'].forEach(m => {
      const o = document.createElement('option');
      o.value = m; o.textContent = MODE_LABELS[m];
      sel.append(o);
    });
    sel.value = 'textured';
  }

  // ── Initialize viewer ──
  const viewerContainer = $('#viewer');
  try {
    const { createViewer, setViewerToken } = await import('/viewer.js');
    setViewerToken(token);

    viewer = await createViewer(
      viewerContainer,
      j.id,
      reps || { textured: { available: true, url: `/api/jobs/${j.id}/files/mesh/model.glb` } },
      metric,
      { measureLabel: $('#measurement') }
    );

    // Sync selector to actual loaded mode
    if (viewer && sel.value) {
      // The viewer auto-loads via fallback; update selector to match
    }

    // Representation switching
    let switching = false;
    sel.onchange = async (e) => {
      if (switching) return;
      switching = true;
      const prev = sel.value;
      try {
        await viewer.loadMode(e.target.value);
      } catch (err) {
        toast(`Could not load ${MODE_LABELS[e.target.value]}: ${err.message}`);
        sel.value = prev;
      } finally {
        switching = false;
      }
    };

    // Reset view
    $('#reset-view').onclick = () => viewer.resetView();

    // Wireframe toggle (applicable to mesh modes)
    $('#wireframe-btn').onclick = () => viewer.wireframe();

    // Measurement tools
    document.querySelectorAll('[data-mode]').forEach(b => b.onclick = () => {
      if (b.disabled) return;
      document.querySelectorAll('[data-mode]').forEach(x => x.classList.toggle('active', x === b));
      viewer.setMode(b.dataset.mode);
    });
    $('#clear-measure').onclick = () => viewer.clear();

  } catch (e) {
    const el = document.createElement('p');
    el.className = 'notice';
    el.style.margin = '100px 20px';
    el.textContent = '3D viewer could not initialize: ' + e.message + '. Download the GLB bundle from the Export Center.';
    viewerContainer.append(el);
  }
}

refresh();setInterval(()=>{if(!activeJob)refresh();},15000);


  async function initMap(jid) {
    const notice = document.getElementById('map-notice');
    const container = document.getElementById('map-container');
    const metrics = document.getElementById('map-metrics');
    const coords = document.getElementById('map-coords');
    
    try {
      const res = await fetch(`/api/jobs/${jid}/map-data`);
      if (!res.ok) throw new Error('Failed to fetch map data');
      const data = await res.json();
      
      if (data.metric_state !== 'GEOREFERENCED_METRIC') {
         notice.style.display = 'block';
         notice.innerText = "Georeferenced map unavailable because real-world alignment was not established.";
         return;
      }
      
      container.style.display = 'block';
      metrics.innerHTML = `
        <div><span>CRS</span><strong>${data.crs || 'Unknown'}</strong></div>
        <div><span>Alignment Quality (RMSE)</span><strong>${data.alignment_quality?.rmse_m?.toFixed(3) || 'N/A'} m</strong></div>
        <div><span>Inliers</span><strong>${data.alignment_quality?.inliers || 0}/${data.alignment_quality?.samples || 0}</strong></div>
      `;
      
      if (!window.leafletMap) {
          window.leafletMap = L.map('leaflet-map');
          
          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
             attribution: '&copy; OpenStreetMap contributors'
          }).addTo(window.leafletMap);
          
          // Coordinate readout
          window.leafletMap.on('mousemove', (e) => {
             coords.innerText = `Lat: ${e.latlng.lat.toFixed(6)}, Lon: ${e.latlng.lng.toFixed(6)}`;
          });
      }
      
      // Clear previous layers if any
      window.leafletMap.eachLayer((layer) => {
          if (layer instanceof L.TileLayer === false) {
              window.leafletMap.removeLayer(layer);
          }
      });
      
      // Draw GPS Trajectory
      if (data.gps_trajectory && data.gps_trajectory.length > 0) {
         const gpsPts = data.gps_trajectory.map(pt => [pt.lat, pt.lon]);
         L.polyline(gpsPts, {color: '#ff4444', weight: 3}).addTo(window.leafletMap);
         data.gps_trajectory.forEach(pt => {
             const circle = L.circleMarker([pt.lat, pt.lon], {radius: 4, color: '#ff4444', fillOpacity: 0.8}).addTo(window.leafletMap);
             circle.bindPopup(`<b>GPS</b><br>Lat: ${pt.lat.toFixed(6)}<br>Lon: ${pt.lon.toFixed(6)}<br>Alt: ${pt.alt.toFixed(2)}<br>Time: ${pt.timestamp}`);
         });
      }
      
      // Draw Reconstructed Trajectory
      if (data.reconstructed_trajectory && data.reconstructed_trajectory.length > 0) {
         const recPts = data.reconstructed_trajectory.map(pt => [pt.lat, pt.lon]);
         L.polyline(recPts, {color: '#4444ff', weight: 3, dashArray: '5, 5'}).addTo(window.leafletMap);
         data.reconstructed_trajectory.forEach(pt => {
             const circle = L.circleMarker([pt.lat, pt.lon], {radius: 4, color: '#4444ff', fillOpacity: 0.8}).addTo(window.leafletMap);
             circle.bindPopup(`<b>Reconstructed Camera</b><br>ID: ${pt.camera_id}<br>Lat: ${pt.lat.toFixed(6)}<br>Lon: ${pt.lon.toFixed(6)}<br>Alt: ${pt.alt.toFixed(2)}`);
         });
      }
      
      // Fit Bounds
      if (data.mission_bounds) {
         const b = data.mission_bounds;
         window.leafletMap.fitBounds([[b.min_lat, b.min_lon], [b.max_lat, b.max_lon]]);
         
         L.rectangle([[b.min_lat, b.min_lon], [b.max_lat, b.max_lon]], {color: "#ff7800", weight: 1, fillOpacity: 0.1}).addTo(window.leafletMap);
      }
      
      window.window.leafletMap.invalidateSize();
      
    } catch (e) {
      console.error(e);
      notice.style.display = 'block';
      notice.innerText = "Error loading map data: " + e.message;
    }
  }
