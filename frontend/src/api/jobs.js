import { fetchApi } from './client';

export async function fetchJobs() {
  return fetchApi('/jobs');
}

export async function fetchJob(id) {
  return fetchApi(`/jobs/${id}`);
}

export async function createJob(formData) {
  const token = sessionStorage.getItem('aakar-token');
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch('/api/jobs', {
    method: 'POST',
    headers,
    body: formData,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Upload Error: ${text}`);
  }
  return res.json();
}
