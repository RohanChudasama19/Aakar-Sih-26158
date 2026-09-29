import React, { useRef, useEffect, useState } from 'react';
import { createViewer } from '../../viewer/viewer.js';
import { HeatmapPanel } from './HeatmapPanel.jsx';

export const AeroReconViewer = ({ mission, activeLayer, activeTool, onMeasureUpdate }) => {
  const containerRef = useRef(null);
  const viewerRef = useRef(null);
  const labelRef = useRef(null);
  
  const [clickedFaceIndex, setClickedFaceIndex] = useState(null);

  useEffect(() => {
    if (!containerRef.current || !mission) return;

    let isDisposed = false;

    const initViewer = async () => {
      const representations = mission.representations || [];
      const metric = mission.report?.metric_state || 'RELATIVE';

      try {
        const viewer = await createViewer(containerRef.current, mission.id, representations, metric, {
          onMeasureUpdate: onMeasureUpdate,
          measureLabel: labelRef.current,
          onCanvasClick: (hit) => {
            if (hit && hit.faceIndex !== undefined) {
               setClickedFaceIndex(hit.faceIndex);
            }
          }
        });
        if (isDisposed) {
          viewer.dispose();
        } else {
          viewerRef.current = viewer;
          window.setWireframe = (s) => viewer.wireframe(s);
          window.resetView = () => viewer.resetView();
          // Apply initial layer and tool if viewer is ready
          viewer.loadMode(activeLayer);
          viewer.setMode(activeTool);
        }
      } catch (err) {
        console.error("Viewer initialization error:", err);
      }
    };

    initViewer();

    return () => {
      isDisposed = true;
      if (viewerRef.current) {
        viewerRef.current.dispose();
        viewerRef.current = null;
      }
    };
  }, [mission.id]);

  useEffect(() => {
    if (viewerRef.current) {
      viewerRef.current.loadMode(activeLayer);
    }
  }, [activeLayer]);

  useEffect(() => {
    if (viewerRef.current) {
      viewerRef.current.setMode(activeTool);
    }
  }, [activeTool]);

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'row', position: 'relative' }}>
      <div style={{ flex: 1, position: 'relative', minWidth: 0, height: '100%' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }}></div>
      <div 
        ref={labelRef} 
        style={{
          position: 'absolute',
          bottom: '16px',
          left: '16px',
          color: 'white',
          backgroundColor: 'rgba(0,0,0,0.5)',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '12px',
          pointerEvents: 'none'
        }}
      ></div>
      </div>
      <HeatmapPanel 
         missionId={mission.id} 
         viewer={viewerRef.current}
         clickedFaceIndex={clickedFaceIndex}
      />
    </div>
  );
};
