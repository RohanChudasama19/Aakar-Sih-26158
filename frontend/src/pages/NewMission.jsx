import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, ChevronRight, Activity, Cpu, CheckCircle, AlertTriangle } from 'lucide-react';
import styles from './NewMission.module.css'; // I will define this
import { fetchProjects } from '../api/projects';

export default function NewMission() {
  const [step, setStep] = useState(1);
  const [projects, setProjects] = useState([]);
  const [formData, setFormData] = useState({
    project_id: 'default-legacy-project',
    name: 'New Reconstruction',
    description: '',
    engine: 'fast_quality'
  });
  const [files, setFiles] = useState({
    video: null,
    gps: null,
    flight: null,
    imu: null,
    barometer: null,
    intrinsics: null,
    rtk: null
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  
  const navigate = useNavigate();

  useEffect(() => {
    fetchProjects().then(data => {
      setProjects(data);
      if (data.length > 0 && !data.find(p => p.id === 'default-legacy-project')) {
        setFormData(prev => ({ ...prev, project_id: data[0].id }));
      }
    }).catch(err => console.error('Error fetching projects', err));
  }, []);

  const handleNext = () => {
    setError('');
    if (step === 1 && (!formData.name || !formData.project_id)) {
      setError('Project and Mission Name are required.');
      return;
    }
    if (step === 2 && (!files.video || !files.gps || !files.flight)) {
      setError('Video, GPS, and Flight Metadata are required.');
      return;
    }
    setStep(s => s + 1);
  };

  const handlePrev = () => {
    setError('');
    setStep(s => s - 1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!files.video || !files.gps || !files.flight) return;
    
    setIsSubmitting(true);
    setError('');
    const fd = new FormData();
    fd.append('video', files.video);
    fd.append('gps', files.gps);
    fd.append('flight', files.flight);

    // Optional files (API expects specific names or ignores them)
    if (files.imu) fd.append('imu', files.imu);
    if (files.barometer) fd.append('barometer', files.barometer);
    if (files.intrinsics) fd.append('intrinsics', files.intrinsics);
    if (files.rtk) fd.append('rtk', files.rtk);

    fd.append('name', formData.name);
    fd.append('project_id', formData.project_id);
    // Passing options as JSON string as expected by backend
    fd.append('options', JSON.stringify({ engine: formData.engine, description: formData.description }));

    try {
      const res = await fetch('/api/jobs', {
        method: 'POST',
        body: fd
      });
      if (res.ok) {
        const data = await res.json();
        navigate(`/missions/${data.id}`);
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to submit mission');
        setIsSubmitting(false);
      }
    } catch (err) {
      setError(err.message || 'Error submitting mission');
      setIsSubmitting(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>New Reconstruction Wizard</h1>
        <p className={styles.subtitle}>Create a new mission and process telemetry.</p>
      </div>

      <div className={styles.wizard}>
        <div className={styles.progress}>
          <div className={`${styles.stepIndicator} ${step >= 1 ? styles.active : ''}`}>1. Details</div>
          <ChevronRight size={16} className={styles.separator} />
          <div className={`${styles.stepIndicator} ${step >= 2 ? styles.active : ''}`}>2. Upload</div>
          <ChevronRight size={16} className={styles.separator} />
          <div className={`${styles.stepIndicator} ${step >= 3 ? styles.active : ''}`}>3. Settings</div>
          <ChevronRight size={16} className={styles.separator} />
          <div className={`${styles.stepIndicator} ${step >= 4 ? styles.active : ''}`}>4. Review</div>
        </div>

        {error && <div className={styles.errorBanner}>{error}</div>}

        <div className={styles.formContainer}>
          {step === 1 && (
            <div className={styles.stage}>
              <h3>Project & Mission Details</h3>
              <div className={styles.field}>
                <label>Project *</label>
                <select value={formData.project_id} onChange={e => setFormData({...formData, project_id: e.target.value})} className={styles.input}>
                  {projects.map(p => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                  {projects.length === 0 && <option value="default-legacy-project">Legacy Missions</option>}
                </select>
                <span className={styles.helpText}>Select the overarching project for this mission.</span>
              </div>

              <div className={styles.field}>
                <label>Mission Name *</label>
                <input 
                  type="text" 
                  className={styles.input}
                  value={formData.name}
                  onChange={e => setFormData({...formData, name: e.target.value})}
                  placeholder="Flight 42 - Sector B"
                />
              </div>

              <div className={styles.field}>
                <label>Description (Optional)</label>
                <textarea 
                  className={styles.input}
                  value={formData.description}
                  onChange={e => setFormData({...formData, description: e.target.value})}
                  rows={3}
                />
              </div>
            </div>
          )}

          {step === 2 && (
            <div className={styles.stage}>
              <h3>Required Inputs</h3>
              <div className={styles.uploadGrid}>
                <label className={`${styles.uploadArea} ${files.video ? styles.hasFile : ''}`}>
                  <h4>Drone Video *</h4>
                  <p>{files.video ? files.video.name : 'MP4, MOV (max 8GB)'}</p>
                  <input type="file" hidden accept="video/mp4,video/quicktime" onChange={e => setFiles({...files, video: e.target.files[0]})} />
                </label>
                <label className={`${styles.uploadArea} ${files.gps ? styles.hasFile : ''}`}>
                  <h4>GPS Telemetry *</h4>
                  <p>{files.gps ? files.gps.name : 'CSV Format'}</p>
                  <input type="file" hidden accept=".csv" onChange={e => setFiles({...files, gps: e.target.files[0]})} />
                </label>
                <label className={`${styles.uploadArea} ${files.flight ? styles.hasFile : ''}`}>
                  <h4>Flight Metadata *</h4>
                  <p>{files.flight ? files.flight.name : 'JSON Format'}</p>
                  <input type="file" hidden accept=".json" onChange={e => setFiles({...files, flight: e.target.files[0]})} />
                </label>
              </div>

              <h3 style={{ marginTop: '24px' }}>Optional Sensors (Unsupported Backend marked)</h3>
              <div className={styles.uploadGrid}>
                <label className={`${styles.uploadArea} ${files.imu ? styles.hasFile : ''}`}>
                  <h4>IMU Data</h4>
                  <p>{files.imu ? files.imu.name : '(Not fully processed)'}</p>
                  <input type="file" hidden accept=".csv,.json" onChange={e => setFiles({...files, imu: e.target.files[0]})} />
                </label>
                <label className={`${styles.uploadArea} ${files.barometer ? styles.hasFile : ''}`}>
                  <h4>Barometer</h4>
                  <p>{files.barometer ? files.barometer.name : '(Not fully processed)'}</p>
                  <input type="file" hidden accept=".csv,.json" onChange={e => setFiles({...files, barometer: e.target.files[0]})} />
                </label>
                <label className={`${styles.uploadArea} ${files.rtk ? styles.hasFile : ''}`}>
                  <h4>RTK Logs</h4>
                  <p>{files.rtk ? files.rtk.name : '(Not fully processed)'}</p>
                  <input type="file" hidden accept=".obs,.nav" onChange={e => setFiles({...files, rtk: e.target.files[0]})} />
                </label>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className={styles.stage}>
              <h3>Processing Settings</h3>
              <p className={styles.helpText}>Processing runtimes vary by hardware and frame count. Backend guarantees no specific timeline.</p>
              
              <div className={styles.engineOptions}>
                <div 
                  className={`${styles.engineCard} ${formData.engine === 'fast_quality' ? styles.activeCard : ''}`}
                  onClick={() => setFormData({...formData, engine: 'fast_quality'})}
                >
                  <Cpu size={24} />
                  <div>
                    <h5>FAST_QUALITY V1 (Experimental)</h5>
                    <p>Uses available GPU, balances speed and mesh quality.</p>
                  </div>
                </div>
                <div 
                  className={`${styles.engineCard} ${formData.engine === 'fast_c' ? styles.activeCard : ''}`}
                  onClick={() => setFormData({...formData, engine: 'fast_c'})}
                >
                  <Activity size={24} />
                  <div>
                    <h5>FAST_C (Draft)</h5>
                    <p>CPU fallback available. Fast, lower texture resolution.</p>
                  </div>
                </div>
                <div 
                  className={`${styles.engineCard} ${formData.engine === 'colmap' ? styles.activeCard : ''}`}
                  onClick={() => setFormData({...formData, engine: 'colmap'})}
                >
                  <CheckCircle size={24} />
                  <div>
                    <h5>QUALITY (COLMAP)</h5>
                    <p>Maximum detail. Requires heavy CUDA GPU and significant time.</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {step === 4 && (
            <div className={styles.stage}>
              <h3>Review & Submit</h3>
              <div className={styles.reviewBlock}>
                <p><strong>Project:</strong> {projects.find(p => p.id === formData.project_id)?.name || 'Legacy'}</p>
                <p><strong>Mission Name:</strong> {formData.name}</p>
                <p><strong>Profile:</strong> {formData.engine.toUpperCase()}</p>
                
                <h4 style={{ marginTop: '16px' }}>Attached Files:</h4>
                <ul className={styles.fileList}>
                  <li>Video: {files.video?.name}</li>
                  <li>GPS: {files.gps?.name}</li>
                  <li>Flight: {files.flight?.name}</li>
                  {files.imu && <li>IMU: {files.imu.name}</li>}
                  {files.barometer && <li>Barometer: {files.barometer.name}</li>}
                  {files.rtk && <li>RTK: {files.rtk.name}</li>}
                </ul>
              </div>
              <div className={styles.warningBox}>
                <AlertTriangle size={16} />
                <span>Submitting will queue the job on the background worker. Duplicate submissions are not recommended.</span>
              </div>
            </div>
          )}
        </div>

        <div className={styles.actions}>
          {step > 1 && (
            <button type="button" className={styles.secondaryBtn} onClick={handlePrev} disabled={isSubmitting}>
              Back
            </button>
          )}
          {step < 4 ? (
            <button type="button" className={styles.primaryBtn} onClick={handleNext}>
              Next Step
            </button>
          ) : (
            <button type="button" className={styles.primaryBtn} onClick={handleSubmit} disabled={isSubmitting}>
              {isSubmitting ? 'Starting...' : 'Submit Mission'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
