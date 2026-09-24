import * as Meas from './measurements.js';
const $=s=>document.querySelector(s);
let token=sessionStorage.getItem('aerorecon-token')||'', activeJob=null, streamAbort=null, viewer=null, renderedJob=null;
const headers=()=>token?{Authorization:`Bearer ${token}`} : {};
async function api(path,opts={}){const r=await fetch(path,{...opts,headers:{...headers(),...opts.headers}});if(!r.ok){const e=await r.json().catch(()=>({detail:r.statusText}));throw Error(typeof e.detail==='string'?e.detail:JSON.stringify(e.detail));}return r;}
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function toast(s){$('#toast').textContent=s;$('#toast').hidden=false;setTimeout(()=>$('#toast').hidden=true,5000);}
function newMission(){ $('#upload-error').textContent='';$('#submit-dialog').showModal(); }
['#new-mission','#empty-new','#nav-new'].forEach(x=>{ if($(x)) $(x).onclick=newMission; });
$('#close-submit-drawer').onclick=()=>$('#submit-dialog').close();
['#nav-guide','#sample-guide','#quality-guide'].forEach(x=>{ if($(x)) $(x).onclick=e=>{e.preventDefault();$('#guide-dialog').showModal();}; });
$('#close-guide').onclick=()=>$('#guide-dialog').close();

$('#video-file').onchange=e=>$('#video-name').textContent=e.target.files[0]?.name||'Choose video file';
$('#nav-missions').onclick=closeDetail;$('#refresh').onclick=refresh;
async function refresh(){
  try{
    const [health, allJobs] = await Promise.all([
      (await api('/api/health')).json(),
      (await api('/api/jobs')).json()
    ]);
    
    $('#worker-message').textContent=health.queue.message;
    $('#worker-short').textContent=health.queue.available ? 'Worker connected' : 'Worker offline';
    
    const isDemo = j => (j.name && j.name.toLowerCase().includes('synthetic')) || (j.options && j.options.demo);
    const prodJobs = allJobs.filter(j => !isDemo(j));
    
    $('#count-total').textContent = prodJobs.length;
    
    const jobCountEl = document.getElementById('job-count');
    if(jobCountEl) jobCountEl.textContent = prodJobs.length;
    
    const listCountEl = document.getElementById('list-count');
    if(listCountEl) listCountEl.textContent = String(prodJobs.length).padStart(2,'0');
    
    $('#count-done').textContent = prodJobs.filter(j => j.status === 'completed').length;
    $('#count-running').textContent = prodJobs.filter(j => ['running','queued'].includes(j.status)).length;
    
    $('#empty').hidden = !!allJobs.length;
    
    $('#missions').innerHTML = allJobs.map(j => {
      const demoBadge = isDemo(j) ? '<span class="prov-tag" style="background:var(--warning-bg); color:var(--warning); border-color:var(--warning); margin-left:8px;">SYNTHETIC DEMONSTRATION</span>' : '';
      return `<button class="mission-card" data-id="${j.id}">
        <div class="card-scene">${j.status==='completed'?'-^':'O?'}</div>
        <div class="card-body">
          <h3 style="display:flex; align-items:center;">${esc(j.name)} ${demoBadge}</h3>
          <span class="status ${j.status}">${esc(j.status)}</span>
          <p>${new Date(j.created*1000).toLocaleString()} A ${esc((j.options?.engine || 'UNKNOWN').toUpperCase())}</p>
          <progress max="100" value="${j.progress}"></progress>
        </div>
      </button>`;
    }).join('');
    
    document.querySelectorAll('.mission-card').forEach(e => e.onclick = () => openJob(e.dataset.id));
  } catch(e) {
    $('#worker-message').textContent = e.message;
    $('#worker-short').textContent = 'Connection unavailable';
  }
}
$('#load-sample').onclick=async()=>{const b=$('#load-sample');b.disabled=true;try{for(const [field,name,type]of[['video','sample.mp4','video/mp4'],['gps','gps.csv','text/csv'],['flight','flight.json','application/json']]){const blob=await(await api('/api/samples/'+name)).blob();const transfer=new DataTransfer();transfer.items.add(new File([blob],name,{type}));$(`[name=${field}]`).files=transfer.files;}$('[name=name]').value='Synthetic campus · smoke test';$('[name=engine]').value='cpu';$('[name=max_frames]').value='60';$('#video-name').textContent='sample.mp4 · synthetic test scene';toast('Sample files loaded. Click Start reconstruction.');}catch(e){$('#upload-error').textContent=e.message;}finally{b.disabled=false;}};
$('#upload-form').onsubmit=e=>{e.preventDefault();const button=$('#submit-button');button.disabled=true;$('#upload-error').textContent='';$('#upload-progress').hidden=false;const form=new FormData(e.target);for(const [k,v]of [...form.entries()])if(v instanceof File&&!v.size)form.delete(k);const xhr=new XMLHttpRequest();xhr.open('POST','/api/jobs');if(token)xhr.setRequestHeader('Authorization',`Bearer ${token}`);xhr.upload.onprogress=e=>{const n=e.lengthComputable?100*e.loaded/e.total:0;$('#upload-progress progress').value=n;$('#upload-progress span').textContent=n<100?`Uploading ${Math.round(n)}% · ${(e.loaded/1048576).toFixed(1)} MB transferred`:'Upload transferred · validating inputs and queuing job…';};xhr.onerror=()=>{button.disabled=false;$('#upload-error').textContent='Upload connection failed. Check the server and retry.';};xhr.onload=()=>{button.disabled=false;let data;try{data=JSON.parse(xhr.responseText);}catch{data={detail:'Server returned an unexpected response'};}if(xhr.status>=200&&xhr.status<300){$('#submit-dialog').close();$('#upload-progress').hidden=true;refresh();openJob(data.id);}else{$('#upload-error').textContent=(data.error?.message || data.detail || JSON.stringify(data));}};xhr.send(form);};
const stageNames=['Ingest & prepare','Camera poses','Dense geometry','Mesh & texture','Georeference','Scene report'];
function closeDetail(){activeJob=null;streamAbort?.abort();viewer?.dispose();viewer=null;renderedJob=null;$('#detail').hidden=true;refresh();}

async function openJob(id){
  streamAbort?.abort();
  viewer?.dispose();
  viewer=null;
  renderedJob=null;
  activeJob=id;
  $('#detail').hidden=false;
  
  $('#detail').innerHTML=`
    <div class="mission-view-layout">
      <!-- LEFT: Pipeline Progress -->
      <div class="pipeline-panel">
        <button class="text-button" id="back" style="margin-bottom: 24px;">&larr; Dashboard</button>
        <h3 style="margin-bottom: 16px;">Pipeline State</h3>
        <div class="pipeline-stages" id="pipeline-stages-list">
          <!-- Populated dynamically -->
        </div>
      </div>
      
      <!-- CENTER: Live Reconstruction -->
      <div class="viewport-panel">
        <div class="viewport-header">
          <div>
            <h2 id="detail-name">Loading mission...</h2>
            <div id="job-message" class="status-subtext" style="margin-top: 4px;"></div>
          </div>
          <div class="action-row">
            <button class="text-button" id="btn-cancel" hidden>Cancel</button>
            <button class="text-button" id="btn-retry" hidden>Retry</button>
          </div>
        </div>
        <div class="viewport-container">
           <progress id="job-progress" max="100" value="0" style="position:absolute; top:0; left:0; width:100%; border-radius:0; height:4px; z-index:10; margin:0;"></progress>
           <div id="results" style="width:100%; height:100%; display:flex; flex-direction:column; overflow:hidden;">
             <div class="live-progress-view">
               <div class="spinner"></div>
             </div>
           </div>
        </div>
      </div>
    </div>
  `;
  
  $('#back').onclick=closeDetail;
  try{
    const j=await(await api('/api/jobs/'+id)).json();
    await updateDetail(j);
    if(!['failed','completed','cancelled','RECONSTRUCTION_BLOCKED'].includes(j.status)) watch(id);
  } catch(e) {
    $('#job-message').textContent=e.message;
  }
}

async function watch(id){streamAbort=new AbortController();try{const r=await api(`/api/jobs/${id}/events`,{signal:streamAbort.signal});const reader=r.body.getReader(),decoder=new TextDecoder();let pending='';while(true){const {value,done}=await reader.read();if(done)break;pending+=decoder.decode(value,{stream:true});let n;while((n=pending.indexOf('\n\n'))>=0){const block=pending.slice(0,n);pending=pending.slice(n+2);if(block.startsWith('data: '))await updateDetail(JSON.parse(block.slice(6)));}}}catch(e){if(e.name!=='AbortError'&&activeJob===id){$('#job-message').textContent='Live connection interrupted. Reconnecting…';setTimeout(()=>activeJob===id&&watch(id),3000);}}}

const PIPELINE_STAGES = [
  "VIDEO", "QUALITY ANALYSIS", "ADAPTIVE KEYFRAMES",
  "FEATURE EXTRACTION", "FEATURE MATCHING", "CAMERA POSE / SfM",
  "METRIC REGISTRATION", "DENSE MVS", "POINT CLOUD",
  "SUPPORTED SURFACE", "TEXTURE", "VALIDATION", "EXPORT"
];

function getStageIndex(j) {
  if(j.status === 'completed') return 13;
  if(j.status === 'failed' || j.status === 'cancelled' || j.status === 'RECONSTRUCTION_BLOCKED') return -1;
  const p = j.progress;
  // Heuristic mapping based on 0-100 progress
  if(p < 5) return 0;
  if(p < 10) return 1;
  if(p < 15) return 2;
  if(p < 25) return 3;
  if(p < 35) return 4;
  if(p < 45) return 5;
  if(p < 50) return 6;
  if(p < 60) return 7;
  if(p < 70) return 8;
  if(p < 80) return 9;
  if(p < 90) return 10;
  if(p < 95) return 11;
  return 12;
}

async function updateDetail(j){
  if(activeJob!==j.id) return;
  $('#detail-name').textContent=j.name;
  $('#job-message').textContent=j.message;
  const progressEl = $('#job-progress');
  if(progressEl) progressEl.value=j.progress;
  
  // Update 13-stage pipeline list
  const listEl = $('#pipeline-stages-list');
  if(listEl) {
    const currentIndex = getStageIndex(j);
    listEl.innerHTML = PIPELINE_STAGES.map((s, i) => {
      let stateClass = '';
      if(currentIndex === -1) {
         stateClass = 'failed';
      } else if (i < currentIndex) {
         stateClass = 'done';
      } else if (i === currentIndex) {
         stateClass = 'running';
      }
      return `<div class="pipeline-step ${stateClass}">
        <div class="step-indicator"></div>
        <div class="step-label">${s}</div>
      </div>`;
    }).join('');
  }
  
  $('#btn-cancel').hidden = ['completed','failed','cancelled','RECONSTRUCTION_BLOCKED'].includes(j.status);
  $('#btn-cancel').onclick = async () => { $('#btn-cancel').disabled=true; await api('/api/jobs/'+j.id+'/cancel', {method:'POST'}); refresh(); };
  $('#btn-retry').hidden = !['completed','failed','cancelled','RECONSTRUCTION_BLOCKED'].includes(j.status);
  $('#btn-retry').onclick = async () => { $('#btn-retry').disabled=true; await api('/api/jobs/'+j.id+'/retry', {method:'POST'}); closeDetail(); openJob(j.id); };
  
  if(j.status==='cancelled'){
    $('#results').innerHTML='<div class="notice error">Job cancelled.</div>';
    return;
  }
  if(j.status==='RECONSTRUCTION_BLOCKED'){
    $('#results').innerHTML='<div class="notice" style="background:var(--warning-bg); border-color:var(--warning-border); color:var(--warning);"><h3>Reconstruction Blocked</h3><p><strong>Reason:</strong> '+esc(j.message)+'</p>'+(j.report&&j.report.readiness?'<h4>Readiness Metrics:</h4><pre>'+esc(JSON.stringify(j.report.readiness,null,2))+'</pre>':'')+'<p><strong>Recommendations:</strong> Ensure sharp frames, adequate overlap, and GPS telemetry before retrying.</p></div>';
    return;
  }
  if(j.status==='failed'){
    $('#results').innerHTML='<div class="notice error">Reconstruction stopped. '+esc(j.message)+'<br>Check the capture guide and worker logs before retrying.</div>';
    return;
  }
  if(j.status==='completed' && renderedJob!==j.id){
    renderedJob=j.id;
    await showResults(j);
  }
}

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
      matrixHTML = `<div class="deliverables-grid" style="display:grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap:16px;">
        ${matrix.map(m => `<div class="mission-card" style="padding:16px;">
          <h4 style="margin:0 0 8px 0; color:var(--text-primary); font-size:14px;">${m.Format}</h4>
          <p style="margin:0 0 12px 0; font-size:12px; color:var(--text-secondary);">${m.Purpose}</p>
          <div style="font-size:10px; font-weight:700; padding:4px 8px; border-radius:4px; display:inline-block; background:${m.Verified?'var(--surface-active)':'var(--warning-bg)'}; color:${m.Verified?'var(--accent-primary)':'var(--warning)'};">${m.Verified ? 'VERIFIED' : 'UNVERIFIED'}</div>
        </div>`).join('')}
      </div>`;
    }
  } catch (_) {
    matrixHTML = '<p>Deliverables matrix unavailable.</p>';
  }

  // Fetch representations manifest for viewer
  let reps = null;
  try { reps = await (await api(`/api/jobs/${j.id}/representations`)).json(); } catch (_) {}

  // Generate Provenance metric helper
  const renderMetric = (label, value, provClass, provLabel, desc) => `
    <div style="background:var(--surface); border:1px solid var(--border); padding:16px; border-radius:var(--radius-md);">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
        <span style="font-size:11px; color:var(--text-tertiary); text-transform:uppercase; letter-spacing:0.05em;">${label}</span>
        <span class="prov-tag ${provClass}">${provLabel}</span>
      </div>
      <div style="font-size:24px; font-weight:600; color:var(--text-primary); margin-bottom:8px;">${value}</div>
      <div style="font-size:11px; color:var(--text-secondary); line-height:1.4;">${desc}</div>
    </div>
  `;

  $('#results').innerHTML = `
    <!-- Top toolbar inside viewport -->
    <div style="height:48px; background:var(--surface-alt); border-bottom:1px solid var(--border); display:flex; align-items:center; padding:0 24px; gap:24px; flex-shrink:0;">
      <div class="tabs-header" style="display:flex; gap:24px; border:none; margin:0;">
        <button class="tab-btn active" data-tab="viewer" style="margin:0; padding:16px 0;">3D Workspace</button>
        <button class="tab-btn" data-tab="quality" style="margin:0; padding:16px 0;">Quality Intelligence</button>
        <button class="tab-btn" data-tab="performance" style="margin:0; padding:16px 0;">Performance</button>
        <button class="tab-btn" data-tab="exports" style="margin:0; padding:16px 0;">Export Center</button>
      </div>
      <div style="margin-left:auto; display:flex; gap:12px;">
        <button class="secondary text-button" id="download-report">Raw Report</button>
        <button class="primary text-button" id="download-all">Download All</button>
      </div>
    </div>

    <div style="flex:1; position:relative; overflow:hidden;">
      <!-- VIEWER TAB -->
      <div class="tab-content active" id="tab-viewer" style="height:100%; position:relative;">
        <div id="viewer" style="position:absolute; inset:0;"></div>
        
        <!-- Workspace Floating Controls -->
        <div style="position:absolute; top:24px; left:24px; display:flex; flex-direction:column; gap:12px; z-index:10;">
          <div style="background:var(--viewer-overlay); backdrop-filter:blur(8px); border:1px solid var(--border); border-radius:var(--radius-md); padding:12px;">
            <label style="font-size:10px; color:var(--text-secondary); text-transform:uppercase; margin-bottom:8px; display:block;">Active Layer</label>
            <select id="representation-selector" style="background:var(--surface); border:1px solid var(--border); color:var(--text-primary); padding:6px 12px; border-radius:4px; font-size:12px; width:200px; outline:none;"></select>
          </div>
          
          <div style="background:var(--viewer-overlay); backdrop-filter:blur(8px); border:1px solid var(--border); border-radius:var(--radius-md); padding:12px;">
            <label style="font-size:10px; color:var(--text-secondary); text-transform:uppercase; margin-bottom:8px; display:block;">Analysis Tools</label>
            <div style="display:flex; flex-direction:column; gap:8px;">
              <button class="text-button" id="reset-view" style="justify-content:flex-start; font-size:12px; color:var(--text-primary);">Reset Camera</button>
              <button class="text-button" id="wireframe-btn" style="justify-content:flex-start; font-size:12px; color:var(--text-primary);">Toggle Wireframe</button>
              <div style="height:1px; background:var(--border); margin:4px 0;"></div>
              <button class="text-button" data-mode="distance" style="justify-content:flex-start; font-size:12px; color:var(--text-primary);">3D Distance</button>
              <button class="text-button" data-mode="area" style="justify-content:flex-start; font-size:12px; color:var(--text-primary);">Surface Area</button>
              <button class="text-button" id="clear-measure" style="justify-content:flex-start; font-size:12px; color:var(--danger);">Clear Tools</button>
            </div>
            <div id="measurement" style="margin-top:12px; font-size:11px; color:var(--accent-primary); font-family:monospace; min-height:16px;"></div>
          </div>
        </div>
      </div>

      <!-- QUALITY TAB -->
      <div class="tab-content" id="tab-quality" style="height:100%; overflow-y:auto; padding:32px; background:var(--bg);">
        <h3 style="margin-bottom:24px; font-size:16px; color:var(--text-primary);">Model Quality Center</h3>
        
        <h4 style="margin-bottom:16px; font-size:13px; color:var(--text-secondary); text-transform:uppercase;">Sparse Backend</h4>
        <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(240px, 1fr)); gap:16px; margin-bottom:32px;">
          ${renderMetric('Registered Cameras', r.sparse_registered_images + ' / ' + r.sparse_total_images, 'prov-computed', 'COMPUTED', 'Cameras successfully localized into the global coordinate frame.')}
          ${renderMetric('Sparse Points', r.sparse_points.toLocaleString(), 'prov-computed', 'COMPUTED', 'Distinct 3D tie points triangulated from feature tracks.')}
          ${renderMetric('Mean Reprojection', (r.sparse_mean_reprojection_error?.toFixed(3) || 'N/A') + ' px', 'prov-computed', 'COMPUTED', 'Average sub-pixel error between predicted and observed features.')}
          ${renderMetric('Mean Track Length', r.sparse_mean_track_length?.toFixed(1) || 'N/A', 'prov-computed', 'COMPUTED', 'Average number of cameras observing a single 3D point.')}
        </div>

        <h4 style="margin-bottom:16px; font-size:13px; color:var(--text-secondary); text-transform:uppercase;">Dense Backend</h4>
        <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(240px, 1fr)); gap:16px; margin-bottom:32px;">
          ${renderMetric('Dense Points', r.dense_points.toLocaleString(), 'prov-computed', 'COMPUTED', 'Raw multi-view stereo depth map fusion points.')}
          ${renderMetric('Mesh Faces', r.mesh_faces?.toLocaleString() || 'N/A', 'prov-computed', 'COMPUTED', 'Triangular polygons forming the continuous surface.')}
          ${renderMetric('Largest Component', (r.largest_component_fraction*100).toFixed(1)+'%', 'prov-computed', 'COMPUTED', 'Fraction of mesh faces belonging to the primary connected surface.')}
          ${renderMetric('Texture Coverage', (r.texture_coverage*100).toFixed(1)+'%', 'prov-computed', 'COMPUTED', 'Fraction of generated mesh successfully assigned valid image texture.')}
        </div>
      </div>

      
      <!-- PERFORMANCE TAB -->
      <div class="tab-content" id="tab-performance" style="height:100%; overflow-y:auto; padding:32px; background:var(--bg);">
        <h3 style="margin-bottom:24px; font-size:16px; color:var(--text-primary);">Performance Analysis</h3>
        
        <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(240px, 1fr)); gap:16px; margin-bottom:32px;">
          ${renderMetric('Profile', (j.options?.engine || 'UNKNOWN').toUpperCase(), 'prov-user-configured', 'USER-CONFIGURED', 'The active reconstruction pipeline definition.')}
          ${renderMetric('Total Runtime', j.runtime ? Math.round(j.runtime)+'s' : 'N/A', 'prov-computed', 'COMPUTED', 'End-to-end processing time.')}
          ${j.options.engine.toLowerCase() === 'fast_quality' ? renderMetric('Target Status', (j.runtime && j.runtime <= 900) ? 'PASSED (<= 900s)' : 'OVER TARGET', 'prov-computed', 'COMPUTED', 'FAST_QUALITY V1 target is 15 minutes (900s).') : ''}
        </div>
        
        <h4 style="margin-bottom:16px; font-size:13px; color:var(--text-secondary); text-transform:uppercase;">Pipeline Timeline</h4>
        <div style="background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-md); margin-bottom:32px; overflow:hidden;">
          <table style="width:100%; text-align:left; border-collapse:collapse; font-size:13px;">
            <thead>
              <tr style="background:var(--surface-alt); border-bottom:1px solid var(--border);">
                <th style="padding:12px 16px; color:var(--text-secondary); font-weight:600;">Stage</th>
                <th style="padding:12px 16px; color:var(--text-secondary); font-weight:600;">Runtime</th>
                <th style="padding:12px 16px; color:var(--text-secondary); font-weight:600;">Backend</th>
              </tr>
            </thead>
            <tbody>
              ${(() => {
                const perf = r.performance_profile || r.runtimes || {};
                if(Object.keys(perf).length === 0) return '<tr><td colspan="3" style="padding:16px;">No detailed timeline available.</td></tr>';
                return Object.entries(perf).map(([stage, data]) => {
                  if (typeof data === 'number') {
                     return `<tr style="border-bottom:1px solid var(--border);"><td style="padding:12px 16px; font-weight:500;">${stage}</td><td style="padding:12px 16px; color:var(--text-secondary);">${data.toFixed(1)}s</td><td style="padding:12px 16px; color:var(--text-tertiary);">Default</td></tr>`;
                  }
                  if (data && typeof data === 'object') {
                     return `<tr style="border-bottom:1px solid var(--border);"><td style="padding:12px 16px; font-weight:500;">${stage}</td><td style="padding:12px 16px; color:var(--text-secondary);">${(data.runtime_sec || 0).toFixed(1)}s</td><td style="padding:12px 16px;"><span class="prov-tag">${data.backend || 'Default'}</span></td></tr>`;
                  }
                  return '';
                }).join('');
              })()}
            </tbody>
          </table>
        </div>
        
        <details>
          <summary style="cursor:pointer; font-size:13px; color:var(--text-secondary); margin-bottom:12px;">View raw report</summary>
          <div style="background:var(--surface); border:1px solid var(--border); padding:24px; border-radius:var(--radius-md);">
            <pre style="margin:0; font-family:monospace; font-size:12px; color:var(--text-secondary); background:transparent; border:none; padding:0; white-space:pre-wrap;">${esc(JSON.stringify(r.performance_profile || r.runtimes || {status: "No detailed profile found"}, null, 2))}</pre>
          </div>
        </details>
      </div>

      <!-- EXPORT TAB -->
      <div class="tab-content" id="tab-exports" style="height:100%; overflow-y:auto; padding:32px; background:var(--bg);">
        <h3 style="margin-bottom:24px; font-size:16px; color:var(--text-primary);">Export Center</h3>
        ${matrixHTML}
      </div>
    </div>
  `;

  // Tab switching
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    };
  });

  $('#download-all').onclick = () => download(`/api/jobs/${j.id}/download`, `mission_${j.id}_deliverables.zip`);
  $('#download-report').onclick = () => download(`/api/jobs/${j.id}/files/reports/mission_report.json`, 'mission_report.json');

  // Viewer setup
  const sel = $('#representation-selector');
  if (reps) {
    MODE_ORDER.forEach(mode => {
      const rep = reps[mode];
      const opt = document.createElement('option');
      opt.value = mode;
      opt.textContent = rep?.available ? MODE_LABELS[mode] : `${MODE_LABELS[mode]} [Unavailable]`;
      opt.disabled = !rep?.available;
      sel.append(opt);
    });
    const firstAvail = MODE_ORDER.find(m => reps[m]?.available);
    if (firstAvail) sel.value = firstAvail;
  } else {
    ['textured','mesh'].forEach(m => {
      const o = document.createElement('option'); o.value = m; o.textContent = MODE_LABELS[m]; sel.append(o);
    });
    sel.value = 'textured';
  }

  try {
    const { createViewer, setViewerToken } = await import('/viewer.js');
    setViewerToken(token);
    viewer = await createViewer($('#viewer'), j.id, reps || { textured: { available: true, url: `/api/jobs/${j.id}/files/mesh/model.glb` } }, metric, { measureLabel: $('#measurement') });
    
    let switching = false;
    sel.onchange = async (e) => {
      if (switching) return;
      switching = true;
      const prev = sel.value;
      try { await viewer.loadMode(e.target.value); } catch (err) { toast(`Error: ${err.message}`); sel.value = prev; } finally { switching = false; }
    };

    $('#reset-view').onclick = () => viewer.resetView();
    $('#wireframe-btn').onclick = () => viewer.wireframe();
    document.querySelectorAll('[data-mode]').forEach(b => b.onclick = () => {
      if (b.disabled) return;
      document.querySelectorAll('[data-mode]').forEach(x => x.classList.toggle('active', x === b));
      viewer.setMode(b.dataset.mode);
    });
    $('#clear-measure').onclick = () => viewer.clear();
  } catch (e) {
    $('#viewer').innerHTML = '<div class="notice" style="margin:32px;">3D viewer unavailable: ' + e.message + '</div>';
  }
}


refresh();setInterval(()=>{if(!activeJob)refresh();},15000);
