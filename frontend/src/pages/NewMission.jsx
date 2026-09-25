import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Video, MapPin, Layers, Info } from 'lucide-react';
import styles from './Dashboard.module.css';
import { createJob } from '../api/jobs';

const NewMission = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ name: 'Campus Survey', engine: 'fast_quality' });
  const [files, setFiles] = useState({ video: null, gps: null, flight: null });
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!files.video || !files.gps || !files.flight) {
      setError('Please provide all required files.');
      return;
    }
    setUploading(true);
    setError('');

    const fd = new FormData();
    fd.append('name', formData.name);
    fd.append('options', JSON.stringify({ engine: formData.engine }));
    fd.append('video', files.video);
    fd.append('gps', files.gps);
    fd.append('flight', files.flight);

    try {
      const result = await createJob(fd);
      navigate(`/workspace/${result.job_id}`);
    } catch (e) {
      setError(e.message);
      setUploading(false);
    }
  };

  return (
    <div className={styles.container}>
      <header style={{ marginBottom: '24px' }}>
        <h1 style={{ color: 'var(--text-primary)' }}>New Reconstruction</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Configure mission inputs and processing strategy.</p>
      </header>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        <div className={styles.missionCard} style={{ padding: '24px', backgroundColor: 'var(--bg-card)' }}>
          <h3 style={{ marginBottom: '16px' }}>01 Mission Setup</h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
            <label style={{ color: 'var(--text-primary)', fontSize: '13px', fontWeight: '600' }}>Mission Name</label>
            <input 
              type="text" 
              value={formData.name}
              onChange={e => setFormData({ ...formData, name: e.target.value })}
              required 
              style={{
                padding: '10px 12px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                backgroundColor: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                outline: 'none'
              }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ color: 'var(--text-primary)', fontSize: '13px', fontWeight: '600' }}>Processing Profile</label>
            <select 
              value={formData.engine}
              onChange={e => setFormData({ ...formData, engine: e.target.value })}
              style={{
                padding: '10px 12px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                backgroundColor: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                outline: 'none'
              }}
            >
              <option value="fast_quality">FAST_QUALITY V1 (Recommended)</option>
              <option value="fast_c">FAST_C</option>
              <option value="colmap">QUALITY</option>
            </select>
          </div>
        </div>

        <div className={styles.missionCard} style={{ padding: '24px', backgroundColor: 'var(--bg-card)' }}>
          <h3 style={{ marginBottom: '16px' }}>02 Required Inputs</h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
            <div style={{ border: '1px dashed var(--border-color)', borderRadius: '8px', padding: '16px', textAlign: 'center', position: 'relative' }}>
              <Video size={24} color="var(--text-secondary)" style={{ marginBottom: '8px' }} />
              <div style={{ fontWeight: '600', marginBottom: '4px' }}>Drone Video</div>
              <div style={{ fontSize: '11px', color: 'var(--color-warning)', marginBottom: '8px' }}>Required</div>
              <input type="file" accept="video/*" onChange={e => setFiles({ ...files, video: e.target.files[0] })} required style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }} />
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', wordBreak: 'break-all' }}>{files.video ? files.video.name : 'Select video...'}</div>
            </div>

            <div style={{ border: '1px dashed var(--border-color)', borderRadius: '8px', padding: '16px', textAlign: 'center', position: 'relative' }}>
              <MapPin size={24} color="var(--text-secondary)" style={{ marginBottom: '8px' }} />
              <div style={{ fontWeight: '600', marginBottom: '4px' }}>GPS Telemetry</div>
              <div style={{ fontSize: '11px', color: 'var(--color-warning)', marginBottom: '8px' }}>Required</div>
              <input type="file" accept=".csv" onChange={e => setFiles({ ...files, gps: e.target.files[0] })} required style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }} />
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', wordBreak: 'break-all' }}>{files.gps ? files.gps.name : 'Select .csv...'}</div>
            </div>

            <div style={{ border: '1px dashed var(--border-color)', borderRadius: '8px', padding: '16px', textAlign: 'center', position: 'relative' }}>
              <Layers size={24} color="var(--text-secondary)" style={{ marginBottom: '8px' }} />
              <div style={{ fontWeight: '600', marginBottom: '4px' }}>Flight Metadata</div>
              <div style={{ fontSize: '11px', color: 'var(--color-warning)', marginBottom: '8px' }}>Required</div>
              <input type="file" accept=".json" onChange={e => setFiles({ ...files, flight: e.target.files[0] })} required style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }} />
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', wordBreak: 'break-all' }}>{files.flight ? files.flight.name : 'Select .json...'}</div>
            </div>
          </div>
        </div>

        <div className={styles.missionCard} style={{ padding: '24px', backgroundColor: 'var(--bg-card)' }}>
          <h3 style={{ marginBottom: '16px' }}>03 Optional Sensors</h3>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
             <span style={{ padding: '6px 12px', borderRadius: '16px', border: '1px solid var(--border-color)', fontSize: '12px' }}>IMU <span style={{ color: 'var(--text-secondary)' }}>- Not supplied</span></span>
             <span style={{ padding: '6px 12px', borderRadius: '16px', border: '1px solid var(--border-color)', fontSize: '12px' }}>Barometer <span style={{ color: 'var(--text-secondary)' }}>- Not supplied</span></span>
             <span style={{ padding: '6px 12px', borderRadius: '16px', border: '1px solid var(--border-color)', fontSize: '12px' }}>RTK <span style={{ color: 'var(--text-secondary)' }}>- Not supplied</span></span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px', backgroundColor: 'var(--bg-elevated)', borderRadius: '8px' }}>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}><Info size={14} style={{ verticalAlign: 'middle', marginRight: '4px' }} /> Measurements remain unverified until independent validation is available.</p>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {error && <span style={{ color: 'var(--color-danger)', fontSize: '13px' }}>{error}</span>}
            <button 
              type="submit" 
              disabled={uploading}
              style={{
                padding: '10px 24px',
                backgroundColor: 'var(--accent-primary)',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontWeight: '600',
                cursor: uploading ? 'not-allowed' : 'pointer',
                opacity: uploading ? 0.6 : 1
              }}
            >
              {uploading ? 'Uploading...' : 'Start Reconstruction'}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default NewMission;
