import { fetchApi } from './client';

export async function fetchProjects() {
  return fetchApi('/projects');
}

export async function createProject(data) {
  return fetchApi('/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export async function fetchProject(id) {
  return fetchApi(/projects/);
}

export async function updateProject(id, data) {
  return fetchApi(/projects/, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export async function archiveProject(id) {
  return fetchApi(/projects/, { method: 'DELETE' });
}

export async function restoreProject(id) {
  return fetchApi(/projects//restore, { method: 'POST' });
}

export async function fetchProjectMissions(id) {
  return fetchApi(/projects//missions);
}
