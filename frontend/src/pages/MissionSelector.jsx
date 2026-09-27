import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Activity, Download } from 'lucide-react';
import styles from './MissionSelector.module.css';
import { fetchJobs } from '../api/jobs';

export default function MissionSelector({ toolName, toolRoute }) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchJobs().then(data => {
      setJobs(data);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  return (
    <div className={styles.container}>
      <h2>Select a Mission for {toolName}</h2>
      <p className={styles.subtitle}>Choose an active mission to open its {toolName.toLowerCase()} workspace.</p>
      
      {loading ? (
        <div>Loading missions...</div>
      ) : (
        <div className={styles.grid}>
          {jobs.map(j => (
            <div key={j.id} className={styles.card} onClick={() => navigate(`/${toolRoute}/${j.id}`)}>
              <h4>{j.name}</h4>
              <p className={styles.statusLabel}>{j.status.toUpperCase()}</p>
              <span className={styles.idLabel}>{j.id}</span>
            </div>
          ))}
          {jobs.length === 0 && (
            <div style={{ color: 'var(--text-secondary)' }}>No missions found.</div>
          )}
        </div>
      )}
    </div>
  );
}
