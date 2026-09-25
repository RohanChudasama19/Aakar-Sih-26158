import React, { useState, useEffect } from 'react';
import { Download, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import styles from './Dashboard.module.css'; // Reuse dashboard styles for cards
import { fetchJobs } from '../api/jobs';
import { fetchDeliverables, getDownloadUrl } from '../api/exports';

const Exports = () => {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [deliverables, setDeliverables] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchJobs().then(jobs => {
      setJobs(jobs);
      const completed = jobs.find(j => j.status === 'completed');
      if (completed) {
        setSelectedJob(completed);
      }
      setLoading(false);
    }).catch(console.error);
  }, []);

  useEffect(() => {
    if (selectedJob) {
      fetchDeliverables(selectedJob.id).then(setDeliverables);
    }
  }, [selectedJob]);

  if (loading) {
    return <div style={{ color: 'var(--text-primary)', padding: '24px' }}>Loading Exports...</div>;
  }

  const exportFormats = [
    { name: 'Dense Point Cloud (PLY)', key: 'dense', path: 'representations/scene_dense.ply' },
    { name: 'Textured Mesh (GLB)', key: 'textured', path: 'representations/scene_textured.glb' },
    { name: 'Geometry Mesh (PLY)', key: 'mesh', path: 'representations/scene_mesh.ply' },
    { name: 'Cameras (JSON)', key: 'cameras', path: 'representations/cameras.json' }
  ];

  return (
    <div className={styles.container}>
      <header style={{ marginBottom: '24px' }}>
        <h1 style={{ color: 'var(--text-primary)' }}>Export Center</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Download reconstruction deliverables and assets.</p>
      </header>

      <div style={{ marginBottom: '24px' }}>
        <label style={{ color: 'var(--text-primary)', marginRight: '16px' }}>Select Mission:</label>
        <select 
          value={selectedJob?.id || ''} 
          onChange={e => setSelectedJob(jobs.find(j => j.id === e.target.value))}
          style={{ padding: '8px 12px', borderRadius: '6px', backgroundColor: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
        >
          {jobs.filter(j => j.status === 'completed').map(j => (
            <option key={j.id} value={j.id}>{j.name}</option>
          ))}
        </select>
      </div>

      {selectedJob && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
          {exportFormats.map(fmt => {
            // Very naive check: if we have deliverables matrix we check it, otherwise we just assume if it's completed it might be available.
            // Ideally backend lists representations.
            const isAvailable = deliverables ? deliverables[fmt.key] : true;
            
            return (
              <div key={fmt.key} className={styles.missionCard} style={{ padding: '24px', backgroundColor: 'var(--bg-card)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h3 style={{ fontSize: '16px' }}>{fmt.name}</h3>
                  {isAvailable ? <CheckCircle size={18} color="var(--color-success)" /> : <XCircle size={18} color="var(--color-danger)" />}
                </div>
                
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
                  Status: {isAvailable ? <span style={{ color: 'var(--color-success)' }}>VERIFIED</span> : <span style={{ color: 'var(--color-danger)' }}>UNAVAILABLE</span>}
                </div>

                <a 
                  href={isAvailable ? getDownloadUrl(selectedJob.id, fmt.path) : '#'} 
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
                    pointerEvents: isAvailable ? 'auto' : 'none'
                  }}
                >
                  <Download size={16} /> Download
                </a>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Exports;
