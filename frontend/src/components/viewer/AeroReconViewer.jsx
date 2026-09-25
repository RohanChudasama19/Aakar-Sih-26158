import React, { useRef, useEffect } from 'react';
import { createViewer } from '../../viewer/viewer.js';

export const AeroReconViewer = ({ mission, activeLayer, activeTool, onMeasureUpdate }) => {
  const containerRef = useRef(null);
  const viewerRef = useRef(null);
  const labelRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !mission) return;

    let isDisposed = false;

    const initViewer = async () => {
      const representations = mission.representations || [];
      const metric = mission.report?.metric_state || 'RELATIVE';

      try {
        const viewer = await createViewer(containerRef.current, mission.id, representations, metric, {
          onMeasureUpdate: onMeasureUpdate,
          measureLabel: labelRef.current
        });
        if (isDisposed) {
          viewer.dispose();
        } else {
          viewerRef.current = viewer;
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
  }, [mission.id]); // Re-init if mission ID changes

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
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
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
  );
};
