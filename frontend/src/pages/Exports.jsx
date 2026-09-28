import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Download, CheckCircle, XCircle, FileArchive, Check, X } from 'lucide-react';
import styles from './Dashboard.module.css'; // Reuse dashboard styles for cards
import { fetchJob } from '../api/jobs';

const Exports = () => {
  const { jobId } = useParams();
  const [mission, setMission] = useState(null);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      if (!jobId || jobId === 'undefined' || jobId === 'null') { setLoading(false); return; }
      try {
        const j = await fetchJob(jobId);
        setMission(j);
        
        if (j.status === 'completed' || j.status === 'degraded') {
           const res = await fetch('/api/jobs/' + jobId + '/files');
           if (res.ok) {
              const fileList = await res.json();
              setFiles(fileList);
           }
        }
      } catch (error) {
        console.error("Error fetching exports:", error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [jobId]);

  if (loading) return <div style={{ color: 'var(--text-primary)', padding: '24px' }}>Loading Export Center...</div>;

  if (!mission) {
    return (
      <div style={{ color: 'var(--text-primary)', padding: '24px' }}>
        <h2>Mission Not Found</h2>
        <p>Please select a valid mission to view exports.</p>
      </div>
    );
  }

  const exportFormats = [
    { name: 'Dense Point Cloud (PLY)', key: 'dense', path: 'representations/scene_dense.ply' },
    { name: 'Textured Mesh (GLB)', key: 'textured', path: 'representations/scene_textured.glb' },
    { name: 'Geometry Mesh (PLY)', key: 'mesh', path: 'representations/scene_mesh.ply' },
    { name: 'Cameras (JSON)', key: 'cameras', path: 'representations/cameras.json' },
    { name: 'Quality Report (JSON)', key: 'report', path: 'viewer_artifacts.json' },
    { name: 'High-Res Texture (PNG)', key: 'texture', path: 'representations/scene_textured_texture_atlas_final.png' },
    { name: 'FBX Model', key: 'fbx', path: 'representations/scene.fbx' },
    { name: 'LAS Point Cloud', key: 'las', path: 'representations/scene_dense.las' },
    { name: 'Digital Surface Model (GeoTIFF)', key: 'dsm', path: 'representations/dsm.tif' },
    { name: 'Orthomosaic (GeoTIFF)', key: 'ortho', path: 'representations/ortho.tif' },
  ];

  const getFile = (path) => files.find(f => f.name === path || f.name.replace(/\\/g, '/') === path);

  const formatBytes = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={styles.container}>
      <header style={{ marginBottom: '24px' }}>
        <h1 style={{ color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileArchive size={24} color="var(--accent-primary)" />
          Export Center
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>Download reconstruction deliverables and scientific assets.</p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
        {exportFormats.map(fmt => {
          const fileData = getFile(fmt.path);
          const isAvailable = !!fileData && fileData.bytes > 0;
          
          return (
            <div key={fmt.key} className={styles.missionCard} style={{ padding: '24px', backgroundColor: 'var(--bg-card)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '16px', color: 'var(--text-primary)' }}>{fmt.name}</h3>
                {isAvailable ? <CheckCircle size={18} color="var(--color-success)" /> : <XCircle size={18} color="var(--color-danger)" />}
              </div>
              
              <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 16px 0', fontSize: '13px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <li style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Filename</span> <span style={{ color: 'var(--text-primary)' }}>{fmt.path.split('/').pop()}</span>
                </li>
                <li style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Size</span> <span style={{ color: 'var(--text-primary)' }}>{isAvailable ? formatBytes(fileData.bytes) : 'N/A'}</span>
                </li>
                <li style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Availability</span> 
                  {isAvailable ? <span style={{ color: 'var(--color-success)', display: 'flex', alignItems: 'center', gap: '4px' }}><Check size={12}/> VERIFIED</span> : <span style={{ color: 'var(--color-danger)', display: 'flex', alignItems: 'center', gap: '4px' }}><X size={12}/> UNAVAILABLE</span>}
                </li>
                <li style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Coordinates</span> <span style={{ color: 'var(--text-primary)' }}>{isAvailable ? mission.report?.metric_state || 'RELATIVE' : 'N/A'}</span>
                </li>
              </ul>

              <a 
                href={isAvailable ? fileData.url : '#'} 
                download
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '8px 16px',
                  backgroundColor: isAvailable ? 'var(--accent-primary)' : 'var(--bg-secondary)',
                  color: isAvailable ? 'white' : 'var(--text-secondary)',
                  textDecoration: 'none',
                  borderRadius: '4px',
                  pointerEvents: isAvailable ? 'auto' : 'none',
                  opacity: isAvailable ? 1 : 0.5
                }}
              >
                <Download size={16} /> {isAvailable ? 'Download Asset' : 'Not Generated'}
              </a>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Exports;
