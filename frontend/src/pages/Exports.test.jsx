import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import Exports from './Exports';
import * as jobsApi from '../api/jobs';

vi.mock('../api/jobs');

describe('Export Center', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    global.fetch = vi.fn();
  });

  it('renders missing mission state if jobId is undefined', async () => {
    render(<MemoryRouter initialEntries={['/exports/undefined']}><Routes><Route path="/exports/:jobId" element={<Exports />} /></Routes></MemoryRouter>);
    expect(await screen.findByText('Mission Not Found')).toBeTruthy();
  });

  it('renders available and unavailable files correctly', async () => {
    jobsApi.fetchJob.mockResolvedValue({ id: 'job1', status: 'completed', report: { metric_state: 'RELATIVE' } });
    
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([
        { name: 'representations/scene_dense.ply', bytes: 1048576, url: '/download/dense.ply' }
      ])
    });

    render(<MemoryRouter initialEntries={['/exports/job1']}><Routes><Route path="/exports/:jobId" element={<Exports />} /></Routes></MemoryRouter>);
    
    expect(await screen.findByText('Export Center')).toBeTruthy();
    
    // Check available file
    expect(await screen.findByText('scene_dense.ply')).toBeTruthy();
    expect(await screen.findByText('1 MB')).toBeTruthy();
    expect(await screen.findAllByText('VERIFIED')).toBeTruthy();
    
    // Check unavailable file (e.g. FBX)
    expect(await screen.findByText('FBX Model')).toBeTruthy();
    expect(await screen.findAllByText('Not Generated')).toBeTruthy();
  });
});


