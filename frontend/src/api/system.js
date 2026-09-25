import { fetchApi } from './client';

export async function fetchSystemHealth() {
  return fetchApi('/health');
}
