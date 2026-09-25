import { fetchApi } from './client';

export async function fetchDeliverables(jobId) {
  try {
    return await fetchApi(`/jobs/${jobId}/files/reports/deliverables_matrix.json`);
  } catch (err) {
    console.error("No deliverables matrix found:", err);
    return null;
  }
}

export function getDownloadUrl(jobId, artifactPath) {
  return `/api/jobs/${jobId}/files/${artifactPath}`;
}
