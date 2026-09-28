import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { 
  MousePointer2, Ruler, Navigation, SplitSquareVertical, Navigation2, Square, X,
  Video, MapPin, Layers, Share2, Expand, Shrink, LocateFixed, PersonStanding, 
  Plane, ChevronUp, ChevronDown, ChevronLeft, ChevronRight, RotateCcw, RotateCw,
  Gauge, Maximize, Orbit, Crosshair, Box, BoxSelect
} from 'lucide-react';
import { AeroReconViewer } from '../components/viewer/AeroReconViewer';
import styles from './Workspace.module.css';
import { fetchJob } from '../api/jobs';

const Workspace = () => {
  const { jobId } = useParams();
  const [activeTool, setActiveTool] = useState('ORBIT');
  const [activeLayer, setActiveLayer] = useState('textured');
  const [mission, setMission] = useState(null);
  const [loading, setLoading] = useState(true);
  const [speed, setSpeed] = useState(1.0);
  const [showNav, setShowNav] = useState(false);
  const [wireframe, setWireframe] = useState(false);

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
  }, [jobId]);

  if (loading) return <div className={styles.container} style={{ padding: "24px" }}>Loading...</div>;

  if (!mission) {
    return (
      <div className={styles.container} style={{ padding: "24px", color: "var(--text-primary)" }}>
        <h2>Mission Not Found</h2>
      </div>
    );
  }

  const metric = mission.report?.metric_state || 'RELATIVE';
  const metricSafe = metric !== 'RELATIVE';

  const handleNavPress = (f, r, u) => {
    if (window.setViewerJoystick) window.setViewerJoystick(f, r, u);
  };
  
  const setCamSpeed = (s) => {
    setSpeed(s);
    if (window.setViewerSpeed) window.setViewerSpeed(s);
  };
  
  const resetCam = () => {
    setActiveTool('ORBIT');
    if (window.resetView) window.resetView(); 
  };

  return (
    <div className={styles.container}>
      <div className={styles.topBar}>
        <div className={styles.missionInfo}>
          <span className={styles.crumbMuted}>Projects</span>
          <span className={styles.crumbSeparator}>/</span>
          <span className={styles.crumbActive}>{mission.name}</span>
        </div>
      </div>

      <div className={styles.workspaceArea}>
        
        {/* Left Toolbar */}
        <div className={styles.leftToolbar}>
           <div className={styles.toolGroup}>
             <span className={styles.toolGroupLabel}>CAMERA MODES</span>
             <button className={`${styles.toolBtn} ${activeTool === 'ORBIT' ? styles.active : ''}`} onClick={() => setActiveTool('ORBIT')} title="Orbit"><Orbit size={16} /></button>
             <button className={`${styles.toolBtn} ${activeTool === 'FOCUS' ? styles.active : ''}`} onClick={() => setActiveTool('FOCUS')} title="Focus"><Crosshair size={16} /></button>
             <button className={`${styles.toolBtn} ${activeTool === 'WALK' ? styles.active : ''}`} onClick={() => {setActiveTool('WALK'); setShowNav(true);}} title="Walk"><PersonStanding size={16} /></button>
             <button className={`${styles.toolBtn} ${activeTool === 'FLY' ? styles.active : ''}`} onClick={() => {setActiveTool('FLY'); setShowNav(true);}} title="Fly"><Plane size={16} /></button>
           </div>
           
           <div className={styles.toolGroup}>
             <span className={styles.toolGroupLabel}>ANALYSIS</span>
             <button className={`${styles.toolBtn} ${activeTool === 'distance' ? styles.active : ''}`} onClick={() => setActiveTool('distance')} title="Distance"><Ruler size={16} /></button>
             <button className={`${styles.toolBtn} ${activeTool === 'horizontal' ? styles.active : ''}`} onClick={() => setActiveTool('horizontal')} title="Horizontal Distance"><Navigation size={16} /></button>
             <button className={`${styles.toolBtn} ${activeTool === 'vertical' ? styles.active : ''}`} onClick={() => setActiveTool('vertical')} title="Vertical Difference"><SplitSquareVertical size={16} /></button>
             <button className={`${styles.toolBtn} ${activeTool === 'xyz' ? styles.active : ''}`} onClick={() => setActiveTool('xyz')} title="XYZ"><Navigation2 size={16} /></button>
             <button className={`${styles.toolBtn} ${activeTool === 'area' ? styles.active : ''}`} onClick={() => setActiveTool('area')} title="Surface Area"><Square size={16} /></button>
           </div>

           <div className={styles.toolGroup}>
             <span className={styles.toolGroupLabel}>SCENE</span>
             <button className={`${styles.toolBtn} ${activeLayer === 'textured' && !wireframe ? styles.active : ''}`} onClick={() => {setActiveLayer('textured'); setWireframe(false); if(window.setWireframe)window.setWireframe(false);}} title="Textured"><Box size={16} /></button>
             <button className={`${styles.toolBtn} ${activeLayer === 'mesh' && !wireframe ? styles.active : ''}`} onClick={() => {setActiveLayer('mesh'); setWireframe(false); if(window.setWireframe)window.setWireframe(false);}} title="Solid Mesh"><Layers size={16} /></button>
             <button className={`${styles.toolBtn} ${wireframe ? styles.active : ''}`} onClick={() => {setWireframe(true); if(window.setWireframe)window.setWireframe(true);}} title="Wireframe"><BoxSelect size={16} /></button>
             <button className={`${styles.toolBtn} ${activeLayer === 'dense' ? styles.active : ''}`} onClick={() => {setActiveLayer('dense'); setWireframe(false); if(window.setWireframe)window.setWireframe(false);}} title="Point Cloud"><MapPin size={16} /></button>
           </div>

           <div className={styles.toolGroup}>
             <span className={styles.toolGroupLabel}>ACTIONS</span>
             <button className={styles.toolBtn} onClick={() => { if(window.viewerZoom) window.viewerZoom(1); }} title="Zoom In"><Expand size={16} /></button>
             <button className={styles.toolBtn} onClick={() => { if(window.viewerZoom) window.viewerZoom(-1); }} title="Zoom Out"><Shrink size={16} /></button>
             <button className={styles.toolBtn} onClick={() => { resetCam(); }} title="Reset / Fit Model"><LocateFixed size={16} /></button>
           </div>
        </div>

        <div className={styles.viewport}>
          {mission.status === 'completed' || mission.status === 'degraded' ? (
            <AeroReconViewer 
              mission={mission}
              activeLayer={activeLayer}
              activeTool={activeTool}
              onMeasureUpdate={() => {}}
            />
          ) : (
             <div className={styles.viewportMockup}>Processing...</div>
          )}

          {/* Nav Overlay */}
          {showNav && (
            <div className={styles.navOverlay}>
               <div className={styles.navHeader}>
                 <span>Navigation</span>
                 <button onClick={() => {setShowNav(false); setActiveTool('ORBIT');}}><X size={14}/></button>
               </div>
               
               <div className={styles.navSpeed}>
                  <button onClick={() => setCamSpeed(0.5)} className={speed === 0.5 ? styles.active : ''}>Slow</button>
                  <button onClick={() => setCamSpeed(1.0)} className={speed === 1.0 ? styles.active : ''}>Norm</button>
                  <button onClick={() => setCamSpeed(3.0)} className={speed === 3.0 ? styles.active : ''}>Fast</button>
               </div>

               <div className={styles.dpadGroup}>
                 <div className={styles.dpadRow}>
                   <button onPointerDown={()=>handleNavPress(0,0,1)} onPointerUp={()=>handleNavPress(0,0,0)} onPointerLeave={()=>handleNavPress(0,0,0)} title="Ascend">U</button>
                   <button onPointerDown={()=>handleNavPress(1,0,0)} onPointerUp={()=>handleNavPress(0,0,0)} onPointerLeave={()=>handleNavPress(0,0,0)} title="Forward"><ChevronUp/></button>
                   <button onPointerDown={()=>handleNavPress(0,0,-1)} onPointerUp={()=>handleNavPress(0,0,0)} onPointerLeave={()=>handleNavPress(0,0,0)} title="Descend">D</button>
                 </div>
                 <div className={styles.dpadRow}>
                   <button onPointerDown={()=>handleNavPress(0,-1,0)} onPointerUp={()=>handleNavPress(0,0,0)} onPointerLeave={()=>handleNavPress(0,0,0)} title="Left"><ChevronLeft/></button>
                   <button onPointerDown={()=>handleNavPress(-1,0,0)} onPointerUp={()=>handleNavPress(0,0,0)} onPointerLeave={()=>handleNavPress(0,0,0)} title="Backward"><ChevronDown/></button>
                   <button onPointerDown={()=>handleNavPress(0,1,0)} onPointerUp={()=>handleNavPress(0,0,0)} onPointerLeave={()=>handleNavPress(0,0,0)} title="Right"><ChevronRight/></button>
                 </div>
               </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Workspace;
