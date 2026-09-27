import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import ProjectList from './ProjectList';
import * as api from '../api/projects';
import { vi, describe, it, expect, beforeEach } from 'vitest';

vi.mock('../api/projects');

describe('ProjectList', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('renders loading state initially', () => {
    api.fetchProjects.mockReturnValue(new Promise(() => {}));
    render(<BrowserRouter><ProjectList /></BrowserRouter>);
    expect(screen.getByText(/Loading projects\.\.\./i)).toBeInTheDocument();
  });

  it('renders empty state when no projects', async () => {
    api.fetchProjects.mockResolvedValue([]);
    render(<BrowserRouter><ProjectList /></BrowserRouter>);
    await waitFor(() => {
      expect(screen.getByText(/No Projects Yet/i)).toBeInTheDocument();
    });
  });

  it('renders projects and supports creating a new one', async () => {
    api.fetchProjects.mockResolvedValue([
      { id: 'proj-1', name: 'Test Proj', mission_count: 5, created_at: Date.now() / 1000 }
    ]);
    api.createProject.mockResolvedValue({ id: 'proj-2', name: 'New Proj' });

    render(<BrowserRouter><ProjectList /></BrowserRouter>);
    
    await waitFor(() => {
      expect(screen.getByText('Test Proj')).toBeInTheDocument();
    });

    const createBtn = screen.getByRole('button', { name: /New Project/i });
    await userEvent.click(createBtn);

    expect(screen.getByText(/Create New Project/i)).toBeInTheDocument();

    const input = screen.getByLabelText(/Project Name/i);
    await userEvent.type(input, 'New Proj');

    const submitBtn = screen.getByRole('button', { name: 'Create' });
    await userEvent.click(submitBtn);

    expect(api.createProject).toHaveBeenCalledWith({
      name: 'New Proj',
      description: '',
      location: ''
    });
  });
});
