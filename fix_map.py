from pathlib import Path

p = Path("web/app.js")
js = p.read_text(encoding="utf-8")

# Find the tab switching logic
old_tab_logic = '''
  // Tab switching
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    };
  });
'''

new_tab_logic = '''
  // Tab switching
  let leafletMap = null;
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
      
      if (btn.dataset.tab === 'map') {
         if (!leafletMap) {
            initMap(j.id);
         } else {
            leafletMap.invalidateSize();
         }
      }
    };
  });

  async function initMap(jid) {
    const notice = document.getElementById('map-notice');
    const container = document.getElementById('map-container');
    const metrics = document.getElementById('map-metrics');
    const coords = document.getElementById('map-coords');
    
    try {
      const res = await fetch(/api/jobs//map-data);
      if (!res.ok) throw new Error('Failed to fetch map data');
      const data = await res.json();
      
      if (data.metric_state !== 'GEOREFERENCED_METRIC') {
         notice.style.display = 'block';
         notice.innerText = "Georeferenced map unavailable because real-world alignment was not established.";
         return;
      }
      
      container.style.display = 'block';
      metrics.innerHTML = 
        <div><span>CRS</span><strong></strong></div>
        <div><span>Alignment Quality (RMSE)</span><strong> m</strong></div>
        <div><span>Inliers</span><strong>/</strong></div>
      ;
      
      // Initialize Leaflet Map
      leafletMap = L.map('leaflet-map');
      
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
         attribution: '&copy; OpenStreetMap contributors'
      }).addTo(leafletMap);
      
      // Coordinate readout
      leafletMap.on('mousemove', (e) => {
         coords.innerText = Lat: , Lon: ;
      });
      
      // Draw GPS Trajectory
      if (data.gps_trajectory && data.gps_trajectory.length > 0) {
         const gpsPts = data.gps_trajectory.map(pt => [pt.lat, pt.lon]);
         L.polyline(gpsPts, {color: '#ff4444', weight: 3}).addTo(leafletMap);
         data.gps_trajectory.forEach(pt => {
             const circle = L.circleMarker([pt.lat, pt.lon], {radius: 4, color: '#ff4444', fillOpacity: 0.8}).addTo(leafletMap);
             circle.bindPopup(<b>GPS</b><br>Lat: <br>Lon: <br>Alt: <br>Time: );
         });
      }
      
      // Draw Reconstructed Trajectory
      if (data.reconstructed_trajectory && data.reconstructed_trajectory.length > 0) {
         const recPts = data.reconstructed_trajectory.map(pt => [pt.lat, pt.lon]);
         L.polyline(recPts, {color: '#4444ff', weight: 3, dashArray: '5, 5'}).addTo(leafletMap);
         data.reconstructed_trajectory.forEach(pt => {
             const circle = L.circleMarker([pt.lat, pt.lon], {radius: 4, color: '#4444ff', fillOpacity: 0.8}).addTo(leafletMap);
             circle.bindPopup(<b>Reconstructed Camera</b><br>ID: <br>Lat: <br>Lon: <br>Alt: );
         });
      }
      
      // Fit Bounds
      if (data.mission_bounds) {
         const b = data.mission_bounds;
         leafletMap.fitBounds([[b.min_lat, b.min_lon], [b.max_lat, b.max_lon]]);
         
         // Draw mission footprint as a simple rectangle overlay
         L.rectangle([[b.min_lat, b.min_lon], [b.max_lat, b.max_lon]], {color: "#ff7800", weight: 1, fillOpacity: 0.1}).addTo(leafletMap);
      }
      
      leafletMap.invalidateSize();
      
    } catch (e) {
      console.error(e);
      notice.style.display = 'block';
      notice.innerText = "Error loading map data: " + e.message;
    }
  }
'''

js = js.replace(old_tab_logic.strip(), new_tab_logic.strip())
p.write_text(js, encoding="utf-8")
