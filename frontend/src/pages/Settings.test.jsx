import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import React from 'react';
import Settings from './Settings';
import { ThemeProvider } from '../context/ThemeContext';

describe('System Settings', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    global.fetch = vi.fn((url) => {
      if (url === '/api/health') return Promise.resolve({ ok: true, json: () => Promise.resolve({ status: 'ok', queue: { status: 'running', workers_online: 1 }, capabilities: { colmap: true } }) });
      if (url === '/api/system/info') return Promise.resolve({ ok: true, json: () => Promise.resolve({ data_dir: '/data', disk_used: 1024, disk_total: 2048, colmap_path: '/usr/bin/colmap' }) });
      return Promise.reject();
    });
    localStorage.clear();
  });

  const renderWithTheme = (ui) => {
    return render(
      <ThemeProvider>
        {ui}
      </ThemeProvider>
    );
  };

  it('renders and fetches engine diagnostics', async () => {
    renderWithTheme(<Settings />);
    
    // Switch to Engine tab
    fireEvent.click(await screen.findByText('Reconstruction Engine'));
    
    expect(await screen.findByText('Online')).toBeTruthy(); // API Health
    expect(await screen.findByText('Yes (/usr/bin/colmap)')).toBeTruthy(); // COLMAP
  });

  it('renders storage diagnostics', async () => {
    renderWithTheme(<Settings />);
    
    // Switch to Storage tab
    fireEvent.click(await screen.findByText('Hardware & Storage'));
    
    expect(await screen.findByText('/data')).toBeTruthy(); // data dir
    expect(await screen.findByText('1 KB / 2 KB')).toBeTruthy(); // storage used
  });

  it('persists processing defaults to localStorage', async () => {
    renderWithTheme(<Settings />);
    
    fireEvent.click(await screen.findByText('Processing Defaults'));
    
    const select = await screen.findByRole('combobox');
    fireEvent.change(select, { target: { value: 'FAST' } });
    
    expect(localStorage.getItem('aerorecon_defaults')).toContain('"profile":"FAST"');
  });
});

