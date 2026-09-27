import React, { useState, useEffect } from 'react';
import { Activity, HardDrive, Box, ShieldCheck, ChevronUp, AlertTriangle, Clock } from 'lucide-react';
import { AreaChart, Area, ResponsiveContainer } from 'recharts';
import { useNavigate } from 'react-router-dom';
import styles from './Dashboard.module.css';
import { fetchJobs } from '../api/jobs';

const Dashboard = () => {
  const navigate = useNavigate();
  const [data, setData] = useState({ jobs: [], activeMission: null });
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const jobs = await fetchJobs();
      // Remove mock trends and compute real numbers
      setData({
        jobs: jobs,
        activeMission: jobs.length > 0 ? jobs[0] : null
      });
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const id = setInterval(loadData, 5000);
    return () => clearInterval(id);
  }, []);

  const handleUpload = (e) => {
    e.preventDefault();
    navigate('/new');
  };

  if (loading) {
    return <div style={{ color: 'var(--text-primary)', padding: '24px' }}>Loading Dashboard...</div>;
  }

  const { jobs, activeMission } = data;
  const runningJobs = jobs.filter(j => ['pending', 'running', 'queued', 'preprocessing'].includes(j.status));
  const completedJobs = jobs.filter(j => j.status === 'completed');
  const failedJobs = jobs.filter(j => ['failed', 'cancelled', 'RECONSTRUCTION_BLOCKED'].includes(j.status));
  
  // Fake sparkline just for visual placeholder if real history isn't available
  const sparklineData = Array.from({ length: 10 }, (_, i) => ({ name: i, quality: 60 + Math.random() * 40 }));

  return (
    <div className={styles.container}>
      <div className={styles.kpiGrid}>
        <div className={styles.kpiCard}>
          <div className={styles.kpiHeader}>
            <span className={styles.kpiLabel}>TOTAL MISSIONS</span>
            <Activity className={styles.kpiIcon} size={18} />
          </div>
          <div className={styles.kpiValue}>{jobs.length}</div>
          <div className={styles.kpiTrend}>
            <span className={styles.trendText}>All time</span>
          </div>
        </div>

        <div className={styles.kpiCard}>
          <div className={styles.kpiHeader}>
            <span className={styles.kpiLabel}>ACTIVE / QUEUED</span>
            <HardDrive className={styles.kpiIcon} size={18} />
          </div>
          <div className={styles.kpiValue}>{runningJobs.length}</div>
          <div className={styles.kpiTrend}>
            <span className={styles.trendText}>Processing</span>
          </div>
        </div>

        <div className={styles.kpiCard}>
          <div className={styles.kpiHeader}>
            <span className={styles.kpiLabel}>COMPLETED</span>
            <Box className={styles.kpiIcon} size={18} />
          </div>
          <div className={styles.kpiValue}>{completedJobs.length}</div>
          <div className={styles.kpiTrend}>
            <span className={styles.trendText}>Ready</span>
          </div>
        </div>

        <div className={styles.kpiCard}>
          <div className={styles.kpiHeader}>
            <span className={styles.kpiLabel}>FAILED / BLOCKED</span>
            <ShieldCheck className={styles.kpiIcon} size={18} />
          </div>
          <div className={styles.kpiValue}>{failedJobs.length}</div>
          <div className={styles.kpiTrend}>
            <span className={styles.trendText}>Requires attention</span>
          </div>
        </div>
      </div>

      <div className={styles.missionCard} style={{ marginTop: '24px', padding: '24px', border: '2px dashed var(--border-color)', backgroundColor: 'transparent' }}>
        <h3 style={{ marginBottom: '16px' }}>Start New 3D Reconstruction</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>FAST_QUALITY V1 and QUALITY Colmap pipelines require GPS telemetry and Flight Metadata.</p>
        <button 
          onClick={handleUpload}
          style={{
            padding: '8px 16px',
            backgroundColor: 'var(--accent-primary)',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Navigate to New Reconstruction
        </button>
      </div>

      <div className={styles.mainGrid}>
        {activeMission && (
          <div className={styles.missionCard} onClick={() => navigate(`/missions/${activeMission.id}`)} style={{ cursor: 'pointer' }}>
            <div className={styles.missionHeader}>
              <div>
                <h3>{activeMission.name} {activeMission.id === "b83295bd-9419-485c-bdee-8dce65de4f7c" && <span style={{fontSize: "10px", backgroundColor: "var(--color-danger)", color: "white", padding: "2px 6px", borderRadius: "4px", marginLeft: "8px", verticalAlign: "middle"}}>DIAGNOSTIC / QUALITY FAILED</span>}</h3>
                <span className={styles.missionStatus} style={{ textTransform: 'uppercase' }}>{activeMission.status}</span>
              </div>
              <div className={styles.progressCircle}>{activeMission.progress || 0}%</div>
            </div>
            
            <div className={styles.timeline}>
              <div className={`${styles.timelineStep} ${['pending','queued','running','completed','failed'].includes(activeMission.status) ? styles.completed : ''}`}>
                <div className={styles.stepDot}>1</div>
                <span>Validation</span>
              </div>
              <div className={`${styles.timelineStep} ${['running','completed'].includes(activeMission.status) ? styles.active : ''}`}>
                <div className={styles.stepDot}>2</div>
                <span>Reconstruction</span>
              </div>
              <div className={`${styles.timelineStep} ${activeMission.status === 'completed' ? styles.completed : ''}`}>
                <div className={styles.stepDot}>3</div>
                <span>Export</span>
              </div>
            </div>

            <div className={styles.missionDetails}>
              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>Engine Profile</span>
                <span className={styles.detailValue} style={{ textTransform: 'uppercase' }}>{activeMission.options?.engine || 'UNKNOWN'}</span>
              </div>
              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>State</span>
                <span className={styles.detailValue}>{activeMission.message || '-'}</span>
              </div>
              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>Runtime</span>
                <span className={styles.detailValue}>{activeMission.runtime || '-'} s</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
