import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { HeatmapPanel } from './HeatmapPanel';

global.fetch = vi.fn();

describe('HeatmapPanel', () => {
  it('renders default metrics', () => {
    render(<HeatmapPanel missionId="test-job" viewer={null} />);
    expect(screen.getByText('Original Texture')).toBeInTheDocument();
    expect(screen.getByText('Point Density')).toBeInTheDocument();
  });

  it('handles missing metric reference gracefully', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'NOT_VERIFIED', scientific_limitations: 'Missing GCP' })
    });
    
    const mockViewer = { applyHeatmapColors: vi.fn(), setHeatmapOpacity: vi.fn() };
    render(<HeatmapPanel missionId="test-job" viewer={mockViewer} />);
    fireEvent.click(screen.getByText('Geometric Error'));
    
    await waitFor(() => {
      expect(screen.getByText('NOT_VERIFIED')).toBeInTheDocument();
    });
  });

  it('loads valid metric and parses binary data correctly', async () => {
    const meta = {
      status: 'AVAILABLE',
      num_faces: 2,
      valid_count: 2,
      min: 0.0,
      max: 1.0,
      median: 0.5,
      metric_units: 'points',
      coordinate_state: 'RELATIVE'
    };
    
    const arr = new Float32Array([0.1, 0.9]);
    
    fetch.mockImplementation((url) => {
        if (url.endsWith('metadata')) {
            return Promise.resolve({ ok: true, json: async () => meta });
        }
        return Promise.resolve({ ok: true, arrayBuffer: async () => arr.buffer });
    });
    
    const mockViewer = { applyHeatmapColors: vi.fn(), setHeatmapOpacity: vi.fn() };
    
    render(<HeatmapPanel missionId="test-job" viewer={mockViewer} />);
    fireEvent.click(screen.getByText('Point Density'));
    
    await waitFor(() => {
      expect(mockViewer.applyHeatmapColors).toHaveBeenCalled();
      const callArgs = mockViewer.applyHeatmapColors.mock.calls[0][0];
      if (callArgs) {
          expect(callArgs.length).toBe(18);
      }
    });
  });
});
