// UI Interaction Logic for AeroRecon App Shell

// ── Drawer Management ──
const newMissionBtn = document.getElementById('new-mission');
const emptyNewBtn = document.getElementById('empty-new');
const navNewBtn = document.getElementById('nav-new');

const drawer = document.getElementById('new-mission-drawer');
const overlay = document.getElementById('submit-overlay');
const closeBtn = document.getElementById('close-submit-drawer');
const submitDialog = document.getElementById('submit-dialog'); // native hidden dialog for app.js compat

function openDrawer() {
  overlay.classList.add('open');
  drawer.classList.add('open');
  // Trick app.js if it checks native dialog
  try { submitDialog.showModal(); } catch (e) {}
}

function closeDrawer() {
  overlay.classList.remove('open');
  drawer.classList.remove('open');
  try { submitDialog.close(); } catch (e) {}
}

if(newMissionBtn) newMissionBtn.addEventListener('click', openDrawer);
if(emptyNewBtn) emptyNewBtn.addEventListener('click', openDrawer);
if(navNewBtn) navNewBtn.addEventListener('click', openDrawer);
if(closeBtn) closeBtn.addEventListener('click', closeDrawer);
if(overlay) overlay.addEventListener('click', closeDrawer);

// ── File Input File Name Updates ──
['gps', 'flight'].forEach(name => {
  const el = document.getElementById(name + '-file');
  if(el) {
    el.addEventListener('change', (e) => {
      document.getElementById(name + '-name').textContent = e.target.files[0]?.name || '';
    });
  }
});


// ── Schema Help Drawer ──
const schemaOverlay = document.getElementById('schema-overlay');
const schemaDrawer = document.getElementById('schema-drawer');
const schemaTitle = document.getElementById('schema-title');
const schemaBody = document.getElementById('schema-body');

const schemas = {
  gps: {
    title: 'GPS Telemetry CSV',
    content: `
      <p>Required for metric scale reconstruction and georeferencing.</p>
      <h4>Required Columns:</h4>
      <ul>
        <li><code>timestamp_utc</code> (ISO8601 UTC)</li>
        <li><code>frame</code> (integer)</li>
        <li><code>latitude</code> (WGS84 decimal degrees)</li>
        <li><code>longitude</code> (WGS84 decimal degrees)</li>
        <li><code>altitude_m</code> (meters)</li>
        <li><code>compass_heading_deg</code></li>
        <li><code>gimbal_pitch_deg</code></li>
        <li><code>gimbal_yaw_deg</code></li>
        <li><code>speed_mps</code></li>
        <li><code>satellites</code></li>
      </ul>
      <h4>Example:</h4>
      <pre>timestamp_utc,frame,latitude,longitude,altitude_m,compass_heading_deg,gimbal_pitch_deg,gimbal_yaw_deg,speed_mps,satellites
2024-01-01T12:00:00Z,0,48.749,9.103,412.5,-45,-14,0,5.2,12
2024-01-01T12:00:01Z,30,48.750,9.104,413.0,-45,-14,0,5.2,12
2024-01-01T12:00:02Z,60,48.751,9.105,413.5,-45,-14,0,5.2,12</pre>
      <div style="margin-top:16px;">
        <a href="data:text/csv;charset=utf-8,timestamp_utc,frame,latitude,longitude,altitude_m,compass_heading_deg,gimbal_pitch_deg,gimbal_yaw_deg,speed_mps,satellites%0A" download="gps_template.csv" class="primary" style="font-size:11px; padding:6px 12px;">Download Template</a>
      </div>
    `
  },
  flight: {
    title: 'Flight Metadata JSON',
    content: `
      <p>Defines the mission bounds and basic camera parameters.</p>
      <h4>Required Fields:</h4>
      <pre>{
  "mission_name": "string",
  "drone_model": "string",
  "camera_sensor": "string",
  "video_file": "string",
  "video_resolution": "1920x1080",
  "video_fps": 30.0,
  "video_duration_sec": 60.0,
  "home_point": {
    "latitude": 48.7,
    "longitude": 9.1,
    "altitude_m": 400.0
  },
  "start_time_utc": "2024-01-01T12:00:00Z",
  "end_time_utc": "2024-01-01T12:01:00Z",
  "camera_intrinsics": null
}</pre>
    `
  },
  imu: {
    title: 'IMU Sensor CSV',
    content: `
      <p>Archived for reference. Sensor fusion is currently not implemented.</p>
      <h4>Expected Conceptual Fields:</h4>
      <ul>
        <li><code>timestamp</code></li>
        <li><code>accel_x</code> (m/s²)</li>
        <li><code>accel_y</code></li>
        <li><code>accel_z</code></li>
        <li><code>gyro_x</code> (rad/s)</li>
        <li><code>gyro_y</code></li>
        <li><code>gyro_z</code></li>
      </ul>
    `
  },
  barometer: {
    title: 'Barometer CSV',
    content: `
      <p>Used for relative altitude support if supported by the backend solver.</p>
      <h4>Expected Fields:</h4>
      <ul>
        <li><code>timestamp</code></li>
        <li><code>pressure_hpa</code></li>
        <li><code>relative_altitude_m</code></li>
      </ul>
    `
  },
  intrinsics: {
    title: 'Camera Intrinsics JSON',
    content: `
      <p>Provide exact lens calibration to skip focal length estimation.</p>
      <h4>Supported Camera Models:</h4>
      <p>PINHOLE, SIMPLE_RADIAL, OPENCV</p>
      <h4>Fields:</h4>
      <pre>{
  "camera_model": "PINHOLE",
  "image_width_px": 1920,
  "image_height_px": 1080,
  "fx": 1200.0,
  "fy": 1200.0,
  "cx": 960.0,
  "cy": 540.0,
  "distortion": [0.0, 0.0]
}</pre>
    `
  }
};

window.showHelp = function(type) {
  const schema = schemas[type];
  if(schema) {
    schemaTitle.textContent = schema.title;
    schemaBody.innerHTML = schema.content;
    schemaOverlay.classList.add('open');
    schemaDrawer.classList.add('open');
  }
};

window.closeSchema = function() {
  schemaOverlay.classList.remove('open');
  schemaDrawer.classList.remove('open');
};

if(schemaOverlay) schemaOverlay.addEventListener('click', closeSchema);

// Clean integration: app.js calls .close() on the native dialog on success, so we just listen for it!
submitDialog.addEventListener('close', () => {
  overlay.classList.remove('open');
  drawer.classList.remove('open');
});

schemas.checkpoints = {
    title: "Checkpoints / GCP CSV",
    content: `
      <p>Used for independent spatial accuracy validation or control alignment.</p>
      <div class="notice-box"><svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg> 
      <span><b>CHECKPOINTS</b> are for EVALUATION ONLY and never influence the alignment. <br><b>CONTROL</b> points are used to fit the alignment.</span></div>
      <h4>Required Columns:</h4>
      <ul>
        <li><code>checkpoint_id</code> (string)</li>
        <li><code>latitude</code> (WGS84 decimal degrees)</li>
        <li><code>longitude</code> (WGS84 decimal degrees)</li>
        <li><code>elevation</code> (meters)</li>
        <li><code>role</code> (MUST be either <code>CHECKPOINT</code> or <code>CONTROL</code>)</li>
      </ul>
      <h4>Optional Columns:</h4>
      <p><code>recon_x</code>, <code>recon_y</code>, <code>recon_z</code>, <code>vertical_datum</code>, <code>reference_accuracy_horizontal_m</code>, <code>reference_accuracy_vertical_m</code>, <code>survey_method</code></p>
      <h4>Example:</h4>
      <pre>checkpoint_id,latitude,longitude,elevation,role
CP-01,48.74911,9.10322,412.5,CHECKPOINT
GCP-01,48.74920,9.10350,411.0,CONTROL</pre>
      <div style="margin-top:16px;">
        <a href="data:text/csv;charset=utf-8,checkpoint_id,latitude,longitude,elevation,role%0A" download="checkpoints_template.csv" class="primary" style="font-size:11px; padding:6px 12px;">Download Template</a>
      </div>
    `
};



// -- Native Drag & Drop Visuals --
document.querySelectorAll('.drop-zone').forEach(zone => {
  const input = zone.querySelector('input[type="file"]');
  if (!input) return;
  zone.addEventListener('dragover', (e) => {
    e.preventDefault();
    zone.style.borderColor = 'var(--accent-primary)';
    zone.style.background = '#F2F7F6';
  });
  ['dragleave', 'drop'].forEach(evt => {
    zone.addEventListener(evt, (e) => {
      zone.style.borderColor = '';
      zone.style.background = '';
    });
  });
});
