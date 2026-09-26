import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { 
  Maximize, Minimize, MousePointer2, Move, BoxSelect, 
  MapPin, Layers, Video, Share2, Layers as LayerIcon,
  Ruler, Navigation, SplitSquareVertical, Navigation2, Square, X
} from 'lucide-react';
import { AeroReconViewer } from '../components/viewer/AeroReconViewer';
import styles from './Workspace.module.css';
import { fetchJob } from '../api/jobs';

const Workspace = () => {
  const { jobId } = useParams();
  const [activeTool, setActiveTool] = useState('orbit');
  const [activeLayer, setActiveLayer] = useState('textured');
  const [mission, setMission] = useState(null);
  const [loading, setLoading] = useState(true);
  const [measureData, setMeasureData] = useState([]);

  useEffect(() => {
    const loadMission = async () => {
      if (!jobId || jobId === 'undefined' || jobId === 'null') { setLoading(false); return; }
      try {
        const data = await fetchJob(jobId);
        setMission(data);
      } catch (error) {
        console.error("Error fetching workspace data:", error);
      } finally {
        setLoading(false);
      }
    };

    loadMission();
    
    if (!jobId || jobId === "undefined" || jobId === "null") return;
    
    let es = null;
    const token = sessionStorage.getItem("aerorecon-token") || "";
    const url = token ? `/api/jobs/${jobId}/events?token=${token}` : `/api/jobs/${jobId}/events`;
    
    try {
      es = new EventSource(url);
      es.onmessage = (e) => {
          try {
              const data = JSON.parse(e.data);
              if(data.type === "job_update") setMission(data.job);
          } catch(err){}
      };
    } catch (e) {
      console.error("SSE Error:", e);
    }
    
    const interval = setInterval(loadMission, 30000); // Polling as fallback only
    return () => { 
      if (es) es.close(); 
      clearInterval(interval); 
    };
  }, [jobId]);

  if (!jobId || jobId === "undefined" || jobId === "null") {
    return (
      <div className={styles.container} style={{ padding: "24px", color: "var(--color-danger)" }}>
        <h2>Invalid Mission ID</h2>
        <p>The requested mission ID is invalid.</p>
        <button onClick={() => window.location.href = "/"} className={styles.primaryBtn}>Return to Dashboard</button>
      </div>
    );
  }

  if (loading) {
    return <div className={styles.container} style={{ padding: '24px', color: 'var(--text-primary)' }}>Loading Workspace...</div>;
  }

  if (!mission) {
    return (
      <div className={styles.container} style={{ padding: "24px", color: "var(--text-primary)" }}>
        <h2>Mission Not Found</h2>
        <p>The mission could not be loaded. It may have been deleted or the ID is incorrect.</p>
        <button onClick={() => window.location.href = "/"} className={styles.primaryBtn}>Return to Dashboard</button>
      </div>
    );
  }

  const getStepIcon = (name) => {
    if (name.includes('VIDEO') || name.includes('FRAME')) return <Video size={14} />;
    if (name.includes('CAMERA') || name.includes('ESTIMATION')) return <MapPin size={14} />;
    if (name.includes('DEPTH')) return <LayerIcon size={14} />;
    return <Layers size={14} />;
  };

  const handleMeasureUpdate = (points, mode) => {
    // Viewer handles internal measurement state, we just trigger UI updates if necessary.
    // In legacy viewer, it displays values on the canvas, we could also capture them here if we wanted side-panel display.
  };

  const metric = mission.report?.metric_state || 'RELATIVE';
  const metricSafe = metric !== 'RELATIVE';

  return (
    <div className={styles.container}>
      <div className={styles.actionBar}>
        <div className={styles.breadcrumb}>
          <span className={styles.crumbMuted}>Projects</span>
          <span className={styles.crumbSeparator}>/</span>
          <span className={styles.crumbActive}>{mission.name}</span>
        </div>
        <div className={styles.actionButtons}>
          <button className={styles.iconBtn}><Share2 size={16} /> Share</button>
          <button className={styles.primaryBtn}>Export Options</button>
        </div>
      </div>

      <div className={styles.workspaceGrid}>
        
        <div className={styles.pipelinePanel}>
          <div className={styles.panelHeader}>
            <h3>Reconstruction Pipeline</h3>
            <span className={`${styles.statusBadge} ${styles[mission.status]}`}>{mission.status}</span>
          </div>
          
          <div className={styles.pipelineList}>
            <div className={`${styles.pipelineStep} ${['completed','failed'].includes(mission.status) ? styles.done : styles.active}`}>
              <div className={styles.stepIcon}>{getStepIcon('ESTIMATION')}</div>
              <div className={styles.stepInfo}>
                <span className={styles.stepName}>Processing</span>
                <span className={styles.stepTime}>{mission.runtime}s</span>
              </div>
            </div>
            
            <div className={`${styles.pipelineStep} ${mission.status === 'completed' ? styles.done : styles.pending}`}>
              <div className={styles.stepIcon}>{getStepIcon('MESH')}</div>
              <div className={styles.stepInfo}>
                <span className={styles.stepName}>Mesh Generation</span>
                <span className={styles.stepTime}>-</span>
              </div>
            </div>
          </div>
        </div>

        <div className={styles.viewport}>
          {mission.status === 'completed' ? (
            <AeroReconViewer 
              mission={mission}
              activeLayer={activeLayer}
              activeTool={activeTool}
              onMeasureUpdate={handleMeasureUpdate}
            />
          ) : (
            <div className={styles.viewportMockup}>
              <div className={styles.pointCloudContainer}>
                <div className={styles.gridPlane}></div>
                <div className={styles.dronePath}>
                  <div className={styles.droneMarker}></div>
                </div>
                <div className={styles.geometryMockup}>
                  <div className={styles.building}></div>
                </div>
                <div className={styles.progressOverlay}>
                  <span>{mission.progress || 0}% Complete</span>
                  <div className={styles.progressBar}>
                    <div className={styles.progressFill} style={{ width: `${mission.progress || 0}%` }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className={styles.toolbar}>
            <button className={`${styles.toolBtn} ${activeTool === 'orbit' ? styles.active : ''}`} onClick={() => setActiveTool('orbit')} title="Orbit Tool"><MousePointer2 size={16} /></button>
            <div className={styles.toolbarDivider}></div>
            <button className={`${styles.toolBtn} ${activeTool === 'distance' ? styles.active : ''}`} onClick={() => setActiveTool('distance')} title="3D Distance"><Ruler size={16} /></button>
            <button className={`${styles.toolBtn} ${activeTool === 'horizontal' ? styles.active : ''}`} onClick={() => setActiveTool('horizontal')} title="Horizontal Distance"><Navigation size={16} /></button>
            <button className={`${styles.toolBtn} ${activeTool === 'vertical' ? styles.active : ''}`} onClick={() => setActiveTool('vertical')} title="Vertical Difference"><SplitSquareVertical size={16} /></button>
            <button className={`${styles.toolBtn} ${activeTool === 'xyz' ? styles.active : ''}`} onClick={() => setActiveTool('xyz')} title="XYZ Delta"><Navigation2 size={16} /></button>
            <button className={`${styles.toolBtn} ${activeTool === 'area' ? styles.active : ''}`} onClick={() => setActiveTool('area')} title="Surface Area"><Square size={16} /></button>
            <div className={styles.toolbarDivider}></div>
            <button className={styles.toolBtn} onClick={() => setActiveTool('orbit')} title="Clear Measurement"><X size={16} /></button>
          </div>
        </div>

        <div className={styles.intelligencePanel}>
          <div className={styles.panelHeader}>
            <h3>Intelligence</h3>
          </div>
          
          <div className={styles.panelBody}>
            <div className={styles.layerControl}>
              <span className={styles.sectionLabel}>ACTIVE LAYER</span>
              <div className={styles.layerOptions}>
                <button className={`${styles.layerBtn} ${activeLayer === 'textured' ? styles.active : ''}`} onClick={() => setActiveLayer('textured')}>Textured Mesh</button>
                <button className={`${styles.layerBtn} ${activeLayer === 'mesh' ? styles.active : ''}`} onClick={() => setActiveLayer('mesh')}>Geometry (Wireframe)</button>
                <button className={`${styles.layerBtn} ${activeLayer === 'dense' ? styles.active : ''}`} onClick={() => setActiveLayer('dense')}>Dense Point Cloud</button>
              </div>
            </div>

            <div className={styles.metricsSection}>
              <span className={styles.sectionLabel}>QUALITY METRICS</span>
              
              <div className={styles.metricCard}>
                <div className={styles.metricHeader}>
                  <span>Georeference</span>
                  <span className={`${styles.badge} ${metricSafe ? styles.badgeSuccess : styles.badgeWarning}`}>{metricSafe ? 'VERIFIED' : 'RELATIVE'}</span>
                </div>
                <div className={styles.metricValue}>{mission.report?.metric_state || 'UNKNOWN'}</div>
              </div>

              <div className={styles.metricCard}>
                <div className={styles.metricHeader}>
                  <span>Cameras Registered</span>
                </div>
                <div className={styles.metricValue}>
                  {mission.report?.sparse_registered_images || 0} / {mission.report?.sparse_total_images || 0}
                </div>
              </div>
              
              <div className={styles.metricCard}>
                <div className={styles.metricHeader}>
                  <span>Dense Points</span>
                </div>
                <div className={styles.metricValue}>
                  {mission.report?.dense_points?.toLocaleString() || '-'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Workspace;
