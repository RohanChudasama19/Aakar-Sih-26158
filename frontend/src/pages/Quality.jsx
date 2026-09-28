import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Shield, Activity, Map, Cpu, CheckCircle, AlertTriangle, FileText, Image as ImageIcon, Box } from 'lucide-react';
import { fetchJob } from '../api/jobs';
import styles from './Dashboard.module.css'; // Reusing dashboard styles for cards

const Quality = () => {
  const { jobId } = useParams();
  const [mission, setMission] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadMission = async () => {
      if (!jobId || jobId === 'undefined' || jobId === 'null') { setLoading(false); return; }
      try {
        const data = await fetchJob(jobId);
        setMission(data);
      } catch (error) {
        console.error("Error fetching quality data:", error);
      } finally {
        setLoading(false);
      }
    };
    loadMission();
  }, [jobId]);

  if (loading) return <div style={{ color: 'var(--text-primary)', padding: '24px' }}>Loading Quality Intelligence...</div>;

  if (!mission) {
    return (
      <div style={{ color: 'var(--text-primary)', padding: '24px' }}>
        <h2>Mission Not Found</h2>
        <p>Please select a valid mission to view its Quality Intelligence.</p>
      </div>
    );
  }

  const r = mission.report || {};
  
  // Handlers for missing data
  const valOr = (val, fallback = 'NOT_AVAILABLE') => val !== undefined && val !== null ? val : fallback;
  const numOr = (val, fallback = 'NOT_AVAILABLE') => typeof val === 'number' ? val.toLocaleString(undefined, { maximumFractionDigits: 2 }) : fallback;

  return (
    <div className={styles.container}>
      <header style={{ marginBottom: '24px' }}>
        <h1 style={{ color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Shield size={24} color="var(--accent-primary)" />
          Quality Intelligence
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>Scientific integrity, precision metrics, and validation reports.</p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        
        {/* INPUT QUALITY */}
        <div className={styles.missionCard} style={{ padding: '20px', backgroundColor: 'var(--bg-card)' }}>
          <h3 style={{ fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <ImageIcon size={18} /> Input Quality
          </h3>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '13px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Frames Extracted</span> <span style={{ color: 'var(--text-primary)' }}>{valOr(r.preprocessing?.decoded_frames)}</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Resolution</span> <span style={{ color: 'var(--text-primary)' }}>{r.preprocessing?.width}x{r.preprocessing?.height}</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Blur Rejections</span> <span style={{ color: 'var(--text-primary)' }}>{valOr(r.preprocessing?.blur_rejections)}</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Video Ingestion</span> <span style={{ color: 'var(--text-primary)' }}>{valOr(r.preprocessing?.video_ingestion)}</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Dynamic Masking</span> <span style={{ color: 'var(--text-primary)' }}>{valOr(r.preprocessing?.dynamic_masking ? 'Enabled' : 'Disabled')}</span></li>
          </ul>
        </div>

        {/* OVERLAP AND CONNECTIVITY */}
        <div className={styles.missionCard} style={{ padding: '20px', backgroundColor: 'var(--bg-card)' }}>
          <h3 style={{ fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Activity size={18} /> Overlap & Connectivity
          </h3>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '13px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Registered Cameras</span> <span style={{ color: 'var(--text-primary)' }}>{valOr(r.sfm?.registered_cameras)} / {valOr(r.sfm?.input_frames)}</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Mean Reproj Error</span> <span style={{ color: 'var(--text-primary)' }}>{numOr(r.sfm?.mean_reprojection_error_px)} px</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Mean Track Length</span> <span style={{ color: 'var(--text-primary)' }}>{numOr(r.sfm?.mean_track_length)}</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Sparse Points</span> <span style={{ color: 'var(--text-primary)' }}>{numOr(r.sfm?.sparse_point_count)}</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Registration Ratio</span> <span style={{ color: 'var(--text-primary)' }}>{numOr(r.sfm?.registration_ratio * 100)}%</span></li>
          </ul>
        </div>

        {/* RECONSTRUCTION QUALITY */}
        <div className={styles.missionCard} style={{ padding: '20px', backgroundColor: 'var(--bg-card)' }}>
          <h3 style={{ fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Box size={18} /> Reconstruction Quality
          </h3>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '13px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Dense Points</span> <span style={{ color: 'var(--text-primary)' }}>{numOr(r.dense?.filtered_points)}</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Mesh Vertices</span> <span style={{ color: 'var(--text-primary)' }}>{numOr(r.mesh?.vertices)}</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Mesh Faces</span> <span style={{ color: 'var(--text-primary)' }}>{numOr(r.mesh?.faces)}</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Largest Component</span> <span style={{ color: 'var(--text-primary)' }}>{numOr(r.mesh?.largest_component_area_fraction * 100)}%</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Weak Faces</span> <span style={{ color: 'var(--text-primary)' }}>{numOr(r.mesh?.weak_face_ratio * 100)}%</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Texture Coverage</span> <span style={{ color: 'var(--text-primary)' }}>{numOr(r.mesh?.textured_face_fraction * 100)}%</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--color-warning)' }}><span>Status</span> <span>{valOr(r.mesh?.surface_quality)}</span></li>
          </ul>
        </div>

        {/* GEOSPATIAL ACCURACY */}
        <div className={styles.missionCard} style={{ padding: '20px', backgroundColor: 'var(--bg-card)' }}>
          <h3 style={{ fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Map size={18} /> Geospatial Accuracy
          </h3>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '13px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Coordinate State</span> <span style={{ color: 'var(--text-primary)' }}>{valOr(r.metric_state)}</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>GPS Alignment RMSE</span> <span style={{ color: 'var(--text-primary)' }}>{numOr(r.reprojection_rmse_px)} px</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Reference Dataset</span> <span style={{ color: 'var(--text-primary)' }}>NOT_AVAILABLE</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Independent Accuracy</span> <span style={{ color: 'var(--text-primary)' }}>{valOr(r.alignment?.absolute_accuracy)}</span></li>
          </ul>
        </div>

        {/* PERFORMANCE */}
        <div className={styles.missionCard} style={{ padding: '20px', backgroundColor: 'var(--bg-card)' }}>
          <h3 style={{ fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Cpu size={18} /> Performance
          </h3>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '13px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>SfM Runtime</span> <span style={{ color: 'var(--text-primary)' }}>{numOr(r.sfm?.sfm_runtime_sec)} s</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Dense Runtime</span> <span style={{ color: 'var(--text-primary)' }}>{numOr(r.stages?.C?.elapsed_sec)} s</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Backend Used</span> <span style={{ color: 'var(--text-primary)' }}>{valOr(r.dense?.backend)}</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>GPU Configuration</span> <span style={{ color: 'var(--text-primary)' }}>{valOr(r.hardware?.gpu)} ({valOr(r.hardware?.vram_total_mib)} MB)</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Hardware Provenance</span> <span style={{ color: 'var(--text-primary)' }}>{valOr(r.hardware?.benchmark_verified ? 'VERIFIED' : 'UNVERIFIED')}</span></li>
          </ul>
        </div>

        {/* VALIDATION REPORTS */}
        <div className={styles.missionCard} style={{ padding: '20px', backgroundColor: 'var(--bg-card)', gridColumn: '1 / -1' }}>
          <h3 style={{ fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <FileText size={18} /> Known Warnings and Limitations
          </h3>
          <div style={{ fontSize: '13px', color: 'var(--color-warning)' }}>
            <ul style={{ paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {(r.warnings || []).length > 0 ? (
                r.warnings.map((w, i) => <li key={i}>{w}</li>)
              ) : (
                <li>No warnings recorded.</li>
              )}
            </ul>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Quality;
