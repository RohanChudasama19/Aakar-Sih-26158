import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import Quality from './Quality';
import * as jobsApi from '../api/jobs';

vi.mock('../api/jobs');

describe('Quality Intelligence', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('renders missing mission state if jobId is undefined', async () => {
    render(<MemoryRouter initialEntries={['/quality/undefined']}><Routes><Route path="/quality/:jobId" element={<Quality />} /></Routes></MemoryRouter>);
    expect(await screen.findByText('Mission Not Found')).toBeTruthy();
  });

  it('renders quality metrics from report', async () => {
    jobsApi.fetchJob.mockResolvedValue({
      id: 'job1',
      report: {
        preprocessing: { decoded_frames: 100 },
        sfm: { registered_cameras: 90, input_frames: 100, mean_reprojection_error_px: 1.5 },
        mesh: { surface_quality: 'FRAGMENTED_SURFACE' },
        metric_state: 'RELATIVE'
      }
    });

    render(<MemoryRouter initialEntries={['/quality/job1']}><Routes><Route path="/quality/:jobId" element={<Quality />} /></Routes></MemoryRouter>);
    
    expect(await screen.findByText('Quality Intelligence')).toBeTruthy();
    expect(await screen.findByText('100')).toBeTruthy(); // decoded_frames
    expect(await screen.findByText('90 / 100')).toBeTruthy(); // registered / input
    expect(await screen.findByText('1.5 px')).toBeTruthy(); // reproj error
    expect(await screen.findByText('FRAGMENTED_SURFACE')).toBeTruthy();
    expect(await screen.findByText('RELATIVE')).toBeTruthy();
  });
  
  it('renders fallback for missing metrics', async () => {
    jobsApi.fetchJob.mockResolvedValue({ id: 'job2', report: {} });

    render(<MemoryRouter initialEntries={['/quality/job2']}><Routes><Route path="/quality/:jobId" element={<Quality />} /></Routes></MemoryRouter>);
    
    expect(await screen.findByText('Quality Intelligence')).toBeTruthy();
    const missing = await screen.findAllByText('NOT_AVAILABLE');
    expect(missing.length).toBeGreaterThan(0);
  });
});
