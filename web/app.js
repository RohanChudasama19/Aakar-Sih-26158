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
async function openJob(id){streamAbort?.abort();viewer?.dispose();viewer=null;renderedJob=null;activeJob=id;$('#detail').hidden=false;$('#detail').innerHTML=`<div class="detail-heading"><div><div class="eyebrow">MISSION WORKSPACE</div><h2 id="detail-name">Loading mission…</h2></div><button class="text-button" id="back">← All missions</button></div><div class="system-bar" id="job-message"></div><div class="stage-list">${stageNames.map((s,i)=>`<div class="stage-item" data-stage="${String.fromCharCode(65+i)}"><b>${String.fromCharCode(65+i)}</b>${s}</div>`).join('')}</div><progress id="job-progress" max="100" value="0"></progress><div id="results"></div>`;$('#back').onclick=closeDetail;try{const j=await(await api('/api/jobs/'+id)).json();await updateDetail(j);if(!['failed','completed','cancelled','RECONSTRUCTION_BLOCKED'].includes(j.status))watch(id);}catch(e){$('#job-message').textContent=e.message;}}
async function watch(id){streamAbort=new AbortController();try{const r=await api(`/api/jobs/${id}/events`,{signal:streamAbort.signal});const reader=r.body.getReader(),decoder=new TextDecoder();let pending='';while(true){const {value,done}=await reader.read();if(done)break;pending+=decoder.decode(value,{stream:true});let n;while((n=pending.indexOf('\n\n'))>=0){const block=pending.slice(0,n);pending=pending.slice(n+2);if(block.startsWith('data: '))await updateDetail(JSON.parse(block.slice(6)));}}}catch(e){if(e.name!=='AbortError'&&activeJob===id){$('#job-message').textContent='Live connection interrupted. Reconnecting…';setTimeout(()=>activeJob===id&&watch(id),3000);}}}
async function updateDetail(j){if(activeJob!==j.id)return;$('#detail-name').textContent=j.name;$('#job-message').textContent=j.message;$('#job-progress').value=j.progress;document.querySelectorAll('.stage-item').forEach(e=>{e.className='stage-item';if(j.status==='completed'||e.dataset.stage<j.stage)e.classList.add('done');else if(e.dataset.stage===j.stage)e.classList.add('running');});if(j.status==='RECONSTRUCTION_BLOCKED'){$('#results').innerHTML='<div class="notice" style="background:#fff3cd; color:#856404;"><h3>Reconstruction Blocked</h3><p><strong>Reason:</strong> '+esc(j.message)+'</p>'+(j.report&&j.report.readiness?'<h4>Readiness Metrics:</h4><pre>'+esc(JSON.stringify(j.report.readiness,null,2))+'</pre>':'')+'<p><strong>Recommendations:</strong> Ensure sharp frames, adequate overlap, and GPS telemetry before retrying.</p></div>';return;}if(j.status==='failed'){$('#results').innerHTML='<div class="notice error">Reconstruction stopped. '+esc(j.message)+'<br>Check the capture guide and worker logs before retrying.</div>';return;}if(j.status==='completed'&&renderedJob!==j.id){renderedJob=j.id;await showResults(j);}}
async function download(url,name){try{if(!token){const a=document.createElement('a');a.href=url;a.download=name;a.click();return;}const blob=await(await api(url)).blob();const object=URL.createObjectURL(blob);const a=document.createElement('a');a.href=object;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(object),10000);}catch(e){toast(e.message);}}

async function showResults(j) {
    const r = j.report, metric = r.metric_state === 'GEOREFERENCED_METRIC' || r.metric_state === 'GPS_ALIGNED_UNVERIFIED' || r.metric_state === 'METRIC_SCALE';
    
    // Fetch deliverables matrix if available
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
    } catch (e) {
        matrixHTML = '<p>Deliverables matrix unavailable.</p>';
    }
    
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
            <div class="notice">Surface: ${esc(r.mesh.surface_quality || 'QUALITY NOT ASSESSED')}. ${esc(r.mesh.note)}</div>
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
                <select id="representation-selector">
                    <option value="textured">Textured Mesh</option>
                    <option value="mesh">Mesh (Geometry only)</option>
                    <option value="dense">Dense Point Cloud (Download only)</option>
                    <option value="sparse">Sparse Point Cloud (Download only)</option>
                    <option value="semantic">Semantic View (Download only)</option>
                </select>
            </div>
            <div class="viewer" id="viewer">
                <div class="viewer-label">${metric ? 'METRIC ALIGNMENT (accuracy unverified)' : 'RELATIVE COORDINATES'}<br>Drag to orbit · right drag to pan · scroll to zoom</div>
            </div>
            <div class="viewer-tools">
                <button data-mode="orbit" class="active">Orbit</button>
                <button data-mode="distance" ${metric ? '' : 'disabled title="Requires metric state"'}>Distance</button>
                <button data-mode="area" ${metric ? '' : 'disabled title="Requires metric state"'}>Planar area</button>
                <button id="clear-measure">Clear points</button>
                <button id="wireframe">Wireframe</button>
                <span id="measurement">Choose a measurement tool</span>
            </div>
            <div class="notice">${metric ? 'Measurements use GPS-aligned scale but remain unverified against ground control.' : 'Metric scale is not established. Measurements are disabled or arbitrary.'}</div>
        </div>
        
        <div class="tab-content" id="tab-map">
            <div class="notice">
                ${r.metric_state === 'GEOREFERENCED_METRIC' ? 
                `Georeferenced map alignment established (EPSG: ${r.alignment?.epsg}). Integration with map providers requires configuration.` : 
                'Georeferenced map unavailable because real-world alignment was not established.'}
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
            <h3>Alignment Quality</h3>
            <p><strong>GPS Alignment Residual (RMSE):</strong> ${r.alignment?.rmse_m != null ? r.alignment.rmse_m.toFixed(2) + ' m' : 'N/A'}</p>
            <p><strong>Metric State:</strong> ${esc(r.metric_state)}</p>
            <hr>
            <h3>Independent Spatial Validation</h3>
            <p><strong>Independent Spatial Accuracy:</strong> NOT AVAILABLE</p>
            <small>No independent checkpoints were provided for verification.</small>
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
    
    // Tab switching logic
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

    // 3D Viewer Logic
    try {
        const { createViewer } = await import('/viewer.js');
        const blob = await (await api(`/api/jobs/${j.id}/files/mesh/model.glb`)).arrayBuffer();
        if (activeJob !== j.id) return;
        
        viewer = await createViewer($('#viewer'), blob, metric);
        
        $('#representation-selector').onchange = (e) => {
            if (e.target.value === 'mesh') {
                viewer.wireframe(true);
            } else if (e.target.value === 'textured') {
                viewer.wireframe(false);
            } else {
                toast('That representation is available via download in the Export Center.');
            }
        };

        document.querySelectorAll('[data-mode]').forEach(b => b.onclick = () => {
            if (b.disabled) return;
            document.querySelectorAll('[data-mode]').forEach(x => x.classList.toggle('active', x === b));
            viewer.setMode(b.dataset.mode);
        });
        
        $('#clear-measure').onclick = () => viewer.clear();
        $('#wireframe').onclick = () => viewer.wireframe();
        
    } catch (e) {
        const el = document.createElement('p');
        el.className = 'notice';
        el.style.margin = '100px 20px';
        el.textContent = '3D viewer could not load: ' + e.message + '. Download the GLB bundle to inspect the model locally.';
        $('#viewer').append(el);
    }
}

refresh();setInterval(()=>{if(!activeJob)refresh();},15000);
