import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import NewMission from './NewMission';
import * as projectsApi from '../api/projects';

vi.mock('../api/projects', () => ({
  fetchProjects: vi.fn(),
}));

describe('NewMission Wizard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('navigates through the wizard steps', async () => {
    projectsApi.fetchProjects.mockResolvedValue([
      { id: 'proj-1', name: 'Test Proj' }
    ]);

    render(
      <BrowserRouter>
        <NewMission />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Test Proj')).toBeInTheDocument();
    });

    // Step 1: Details
    expect(screen.getByText(/Project & Mission Details/i)).toBeInTheDocument();
    
    // Fill out details
    const nameInput = screen.getByPlaceholderText('Flight 42 - Sector B');
    await userEvent.type(nameInput, 'Test Mission');

    // Go to step 2
    const nextBtn = screen.getByRole('button', { name: /Next Step/i });
    await userEvent.click(nextBtn);

    // Step 2: Uploads
    expect(screen.getByText(/Required Inputs/i)).toBeInTheDocument();
    // Cannot proceed without files
    await userEvent.click(screen.getByRole('button', { name: /Next Step/i }));
    expect(screen.getByText(/Video, GPS, and Flight Metadata are required/i)).toBeInTheDocument();
  });
});
