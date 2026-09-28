import React, { useState, useEffect } from 'react';
import { getColormapColor, getColorScaleForMetric } from '../../utils/colormaps';

const METRICS = [
  { id: 'ORIGINAL', label: 'Original Texture' },
  { id: 'POINT_DENSITY', label: 'Point Density' },
  { id: 'SURFACE_SUPPORT', label: 'Surface Support' },
  { id: 'POTENTIAL_CAMERA_VISIBILITY', label: 'Potential Camera Visibility' },
  { id: 'RECONSTRUCTION_RISK', label: 'Reconstruction Risk' },
  { id: 'GEOMETRIC_ERROR', label: 'Geometric Error' }
];

export const HeatmapPanel = ({ missionId, viewer, onInspectModeChange, clickedFaceIndex }) => {
  const [activeMetric, setActiveMetric] = useState('ORIGINAL');
  const [opacity, setOpacity] = useState(0.8);
  const [loading, setLoading] = useState(false);
  const [metadata, setMetadata] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [inspectData, setInspectData] = useState(null);
  
  // Cache for loaded values
  const [cache, setCache] = useState({});

  useEffect(() => {
    if (viewer) {
      viewer.setHeatmapOpacity(opacity);
    }
  }, [opacity, viewer]);

  useEffect(() => {
    async function loadHeatmap() {
      if (!viewer) return;
      setErrorMsg(null);
      
      if (activeMetric === 'ORIGINAL') {
        viewer.applyHeatmapColors(null); // Clear heatmap
        setMetadata(null);
        return;
      }

      setLoading(true);
      try {
        const metaRes = await fetch(`/api/jobs/${missionId}/heatmaps/${activeMetric}/metadata`);
        if (!metaRes.ok) {
          throw new Error(metaRes.status === 404 ? 'Artifact not found' : 'Failed to fetch metadata');
        }
        const meta = await metaRes.json();
        
        if (meta.status === 'NOT_VERIFIED' || meta.status === 'UNAVAILABLE') {
          viewer.applyHeatmapColors(null);
          setMetadata(meta);
          setLoading(false);
          return;
        }

        let values = cache[activeMetric];
        if (!values) {
          const binRes = await fetch(`/api/jobs/${missionId}/heatmaps/${activeMetric}`);
          if (!binRes.ok) throw new Error('Failed to fetch binary array');
          const buf = await binRes.arrayBuffer();
          values = new Float32Array(buf);
          setCache(prev => ({ ...prev, [activeMetric]: values }));
        }

        const scale = getColorScaleForMetric(activeMetric);
        const pmin = meta.min;
        const pmax = meta.max;
        
        // Generate vertex colors (3 vertices per face)
        const colors = new Float32Array(meta.num_faces * 3 * 3);
        for (let i = 0; i < meta.num_faces; i++) {
            const v = values[i];
            const rgb = getColormapColor(v, pmin, pmax, scale.invert);
            // v0
            colors[i*9 + 0] = rgb[0]; colors[i*9 + 1] = rgb[1]; colors[i*9 + 2] = rgb[2];
            // v1
            colors[i*9 + 3] = rgb[0]; colors[i*9 + 4] = rgb[1]; colors[i*9 + 5] = rgb[2];
            // v2
            colors[i*9 + 6] = rgb[0]; colors[i*9 + 7] = rgb[1]; colors[i*9 + 8] = rgb[2];
        }

        viewer.applyHeatmapColors(colors);
        viewer.setHeatmapOpacity(opacity);
        setMetadata(meta);
      } catch (err) {
        setErrorMsg(err.message);
        viewer.applyHeatmapColors(null);
        setMetadata(null);
      }
      setLoading(false);
    }
    
    loadHeatmap();
  }, [activeMetric, missionId, viewer]);
  
  useEffect(() => {
     if (clickedFaceIndex !== null && clickedFaceIndex !== undefined && metadata && cache[activeMetric]) {
         const val = cache[activeMetric][clickedFaceIndex];
         setInspectData({
             faceIndex: clickedFaceIndex,
             value: val,
             units: metadata.metric_units,
             status: isNaN(val) ? 'UNKNOWN' : 'VALID'
         });
     } else {
         setInspectData(null);
     }
  }, [clickedFaceIndex, metadata, cache, activeMetric]);

  return (
    <div style={{
      position: 'absolute', top: 16, right: 16, width: 320,
      backgroundColor: '#1e2420', border: '1px solid #4a5c50', 
      borderRadius: 8, padding: 16, color: '#e0e0e0',
      maxHeight: 'calc(100% - 32px)', overflowY: 'auto',
      zIndex: 100, display: 'flex', flexDirection: 'column', gap: 12
    }}>
      <h3 style={{ margin: 0, fontSize: 16, borderBottom: '1px solid #333', paddingBottom: 8 }}>
        Scientific Intelligence
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {METRICS.map(m => (
          <button 
            key={m.id}
            onClick={() => setActiveMetric(m.id)}
            style={{
              padding: '6px 12px', textAlign: 'left',
              backgroundColor: activeMetric === m.id ? '#2e4c3a' : '#2a2a2a',
              color: activeMetric === m.id ? '#fff' : '#ccc',
              border: '1px solid #4a5c50', borderRadius: 4,
              cursor: 'pointer'
            }}
          >
            {m.label}
          </button>
        ))}
      </div>

      {loading && <div style={{ color: '#aaa', fontStyle: 'italic' }}>Loading artifact...</div>}
      
      {errorMsg && (
        <div style={{ backgroundColor: '#4a2020', padding: 8, borderRadius: 4, color: '#ffaaaa' }}>
          {errorMsg}
        </div>
      )}

      {metadata && !loading && (
        <div style={{ backgroundColor: '#2a2a2a', padding: 8, borderRadius: 4, fontSize: 12 }}>
          {metadata.status === 'NOT_VERIFIED' || metadata.status === 'UNAVAILABLE' ? (
            <div style={{ color: '#ffaaaa' }}>
              <strong>{metadata.status}</strong><br/>
              {metadata.scientific_limitations}
            </div>
          ) : (
            <>
              <div style={{ marginBottom: 4 }}><strong>Units:</strong> {metadata.metric_units}</div>
              <div style={{ marginBottom: 4 }}><strong>Scale:</strong> {metadata.coordinate_state}</div>
              <div style={{ marginBottom: 4 }}><strong>Valid Faces:</strong> {metadata.valid_count} / {metadata.num_faces}</div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 12, borderTop: '1px solid #444', paddingTop: 8 }}>
                <span>Min: {metadata.min.toFixed(4)}</span>
                <span>Med: {metadata.median.toFixed(4)}</span>
                <span>Max: {metadata.max.toFixed(4)}</span>
              </div>
              <div style={{ display: 'flex', height: 16, marginTop: 4, background: 'linear-gradient(to right, blue, cyan, green, yellow, red)' }}>
                {/* Visual spectrum */}
              </div>
              
              <div style={{ marginTop: 12 }}>
                <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  Opacity ({Math.round(opacity * 100)}%)
                  <input 
                    type="range" min="0" max="1" step="0.05" 
                    value={opacity} 
                    onChange={e => setOpacity(parseFloat(e.target.value))}
                    style={{ width: '60%' }}
                  />
                </label>
              </div>
              
              <div style={{ marginTop: 12, borderTop: '1px solid #444', paddingTop: 8 }}>
                <a href={`/api/jobs/${missionId}/heatmaps/${activeMetric}`} download style={{ color: '#4CAF50', marginRight: 12, textDecoration: 'none' }}>? Data</a>
                <a href={`/api/jobs/${missionId}/heatmaps/${activeMetric}/metadata`} download style={{ color: '#4CAF50', textDecoration: 'none' }}>? Metadata</a>
              </div>
            </>
          )}
        </div>
      )}
      
      {inspectData && activeMetric !== 'ORIGINAL' && (
         <div style={{ backgroundColor: '#1a1a1a', padding: 8, borderRadius: 4, fontSize: 12, borderLeft: '3px solid #4CAF50' }}>
            <strong>Face ID:</strong> {inspectData.faceIndex}<br/>
            <strong>Value:</strong> {inspectData.value !== undefined ? inspectData.value.toFixed(6) : 'N/A'}<br/>
            <strong>Status:</strong> {inspectData.status}
         </div>
      )}
    </div>
  );
};
