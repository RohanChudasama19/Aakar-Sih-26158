import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Activity, Box, Download, Settings, FileText, CheckCircle, AlertTriangle, XCircle, ArrowLeft } from 'lucide-react';
import styles from './MissionDetail.module.css';
import { fetchJob } from '../api/jobs';

function getStatusDetails(job) {
  if (job.status === 'completed') {
    if (job.report?.mesh?.surface_quality === 'FRAGMENTED_SURFACE' || job.report?.warnings?.length > 0) return { label: 'DEGRADED', icon: AlertTriangle, color: 'var(--color-warning)' };
    return { label: 'COMPLETE', icon: CheckCircle, color: 'var(--color-success)' };
  }
  if (job.status === 'failed') return { label: 'FAILED', icon: XCircle, color: 'var(--color-danger)' };
  if (job.status === 'RECONSTRUCTION_BLOCKED') return { label: 'BLOCKED', icon: XCircle, color: 'var(--color-danger)' };
  if (job.status === 'queued') {
    if (job.stage === 'validating') return { label: 'VALIDATING', icon: Activity, color: 'var(--text-secondary)' };
    if (job.stage) return { label: 'QUEUED', icon: Activity, color: 'var(--text-secondary)' };
    return { label: 'CREATED', icon: Activity, color: 'var(--text-secondary)' };
  }
  if (job.status === 'running') return { label: 'PROCESSING', icon: Activity, color: 'var(--accent-primary)' };
  return { label: job.status.toUpperCase(), icon: Activity, color: 'var(--text-secondary)' };
}

export default function MissionDetail() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // SSE Processing State
  const [liveStatus, setLiveStatus] = useState(null);
  const [liveStage, setLiveStage] = useState(null);
  const [liveProgress, setLiveProgress] = useState(0);
  const [liveMessage, setLiveMessage] = useState('');

  useEffect(() => {
    loadJob();
    // Setup SSE
    const es = new EventSource(`/api/jobs/${jobId}/status`);
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.status) setLiveStatus(data.status);
        if (data.stage) setLiveStage(data.stage);
        if (data.progress !== undefined) setLiveProgress(data.progress);
        if (data.message) setLiveMessage(data.message);
        
        if (['completed', 'failed', 'cancelled', 'RECONSTRUCTION_BLOCKED'].includes(data.status)) {
          es.close();
          loadJob(); // refresh final state
        }
      } catch (err) {}
    };
    es.onerror = () => {
      es.close();
    };

    return () => {
      es.close();
    };
  }, [jobId]);

  const loadJob = async () => {
    try {
      setLoading(true);
      const data = await fetchJob(jobId);
      setJob(data);
      setLiveStatus(data.status);
      setLiveStage(data.stage);
      setLiveProgress(data.progress || 0);
      setLiveMessage(data.message || '');
    } catch (err) {
      setError(err.message || 'Error loading mission');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className={styles.emptyState}>Loading mission details...</div>;
  if (error || !job) return <div className={styles.emptyState}>{error || 'Mission not found'}</div>;

  const currentJobState = {
    ...job, 
    status: liveStatus || job.status,
    stage: liveStage || job.stage,
    progress: liveProgress || job.progress,
    message: liveMessage || job.message
  };

  const statusInfo = getStatusDetails(currentJobState);
  const StatusIcon = statusInfo.icon;
  const isImported = job.report?._provenance === 'IMPORTED_FRAME_BASED_RECONSTRUCTION' || job.project_id === 'default-legacy-project';

  return (
    <div className={styles.container}>
      <button className={styles.backBtn} onClick={() => navigate(`/projects/${job.project_id || ''}`)}>
        <ArrowLeft size={16} /> Back to Project
      </button>

      <div className={styles.header}>
        <div className={styles.headerTitle}>
          <h1>{job.name}</h1>
          <span className={styles.statusBadge} style={{ color: statusInfo.color, borderColor: statusInfo.color }}>
            <StatusIcon size={14} /> {statusInfo.label}
          </span>
          {isImported && <span className={styles.badgeImported}>Imported Mission</span>}
        </div>
        <p className={styles.idLabel}>ID: {job.id}</p>
      </div>

      <div className={styles.grid}>
        <div className={styles.mainCol}>
          
          <div className={styles.card}>
            <h3>Overview</h3>
            <div className={styles.metaGrid}>
              <div>
                <label>Created</label>
                <div>{new Date(job.created * 1000).toLocaleString()}</div>
              </div>
              <div>
                <label>Processing Profile</label>
                <div>{job.options?.engine?.toUpperCase() || 'UNKNOWN'}</div>
              </div>
              <div>
                <label>System Message</label>
                <div style={{ color: 'var(--text-secondary)' }}>{currentJobState.message}</div>
              </div>
              <div>
                <label>Provenance</label>
                <div>{job.report?._provenance || 'AeroRecon Worker pipeline'}</div>
              </div>
            </div>
          </div>

          {(statusInfo.label === 'PROCESSING' || statusInfo.label === 'QUEUED' || statusInfo.label === 'VALIDATING' || statusInfo.label === 'CREATED') && (
            <div className={styles.card}>
              <h3>Processing Monitor</h3>
              <div className={styles.progressBar}>
                <div className={styles.progressFill} style={{ width: `${currentJobState.progress * 100}%` }}></div>
              </div>
              <div className={styles.progressDetails}>
                <span>Stage: {currentJobState.stage || 'Waiting...'}</span>
                <span>{Math.round(currentJobState.progress * 100)}%</span>
              </div>
              <p className={styles.logText}>&gt; {currentJobState.message}</p>
            </div>
          )}

          {statusInfo.label === 'FAILED' && (
            <div className={`${styles.card} ${styles.errorCard}`}>
              <h3>Mission Failed</h3>
              <p><strong>Stage:</strong> {currentJobState.stage || 'Unknown'}</p>
              <p><strong>Diagnostic:</strong> {currentJobState.message || 'No diagnostic message available.'}</p>
              <div className={styles.helpBox}>
                Check your input files for corruption or ensure the selected engine is supported by your hardware.
              </div>
            </div>
          )}

          {statusInfo.label === 'BLOCKED' && (
            <div className={`${styles.card} ${styles.errorCard}`}>
              <h3>Reconstruction Blocked</h3>
              <p><strong>Reason:</strong> {currentJobState.message}</p>
              <p><strong>Readiness Score:</strong> {job.readiness_score}</p>
            </div>
          )}

          {(statusInfo.label === 'COMPLETE' || statusInfo.label === 'DEGRADED') && (
            <div className={styles.card}>
              <h3>Artifacts & Tools</h3>
              <div className={styles.toolsGrid}>
                <button className={styles.toolBtn} onClick={() => navigate(`/workspace/${job.id}`)}>
                  <Box size={24} /> 3D Workspace
                </button>
                <button className={styles.toolBtn} onClick={() => navigate(`/quality/${job.id}`)}>
                  <Activity size={24} /> Quality Intel
                </button>
                <button className={styles.toolBtn} onClick={() => navigate(`/exports/${job.id}`)}>
                  <Download size={24} /> Exports
                </button>
              </div>
              {statusInfo.label === 'DEGRADED' && (
                <div className={styles.warningBox}>
                  <AlertTriangle size={16} />
                  <span>This mission completed with warnings. Artifacts may be degraded. Check Quality Intel.</span>
                </div>
              )}
            </div>
          )}

        </div>
        
        <div className={styles.sideCol}>
          <div className={styles.card}>
            <h3>Input Files</h3>
            <ul className={styles.fileList}>
              <li><FileText size={14}/> Original Video</li>
              <li><FileText size={14}/> GPS Telemetry</li>
              <li><FileText size={14}/> Flight Metadata</li>
            </ul>
          </div>
          
          {(statusInfo.label === 'COMPLETE' || statusInfo.label === 'DEGRADED') && job.report?.stages && (
            <div className={styles.card}>
              <h3>Execution Timings</h3>
              <ul className={styles.timingList}>
                {Object.entries(job.report.stages).map(([stage, info]) => (
                  <li key={stage}>
                    <span>Stage {stage}</span>
                    <span>{Math.round(info.elapsed_sec)}s</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
