import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Database, MapPin } from 'lucide-react';
import styles from './Projects.module.css';
import { fetchProjects, createProject } from '../api/projects';

export default function ProjectList() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [formData, setFormData] = useState({ name: '', description: '', location: '' });
  const navigate = useNavigate();

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const data = await fetchProjects();
      setProjects(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const p = await createProject(formData);
      setShowCreate(false);
      navigate(`/projects/${p.id}`);
    } catch (err) {
      alert(err.message || 'Error creating project');
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>Projects</h1>
        <button className={styles.createBtn} onClick={() => setShowCreate(true)}>
          <Plus size={18} /> New Project
        </button>
      </div>

      {loading ? (
        <div className={styles.emptyState}>Loading projects...</div>
      ) : projects.length === 0 ? (
        <div className={styles.emptyState}>
          <h3>No Projects Yet</h3>
          <p>Create a project to start organizing your reconstructions.</p>
          <button className={styles.createBtn} style={{ margin: '0 auto' }} onClick={() => setShowCreate(true)}>
            <Plus size={18} /> Create Project
          </button>
        </div>
      ) : (
        <div className={styles.grid}>
          {projects.map(p => (
            <div key={p.id} className={styles.card} onClick={() => navigate(`/projects/${p.id}`)}>
              <div className={styles.cardHeader}>
                <h3 className={styles.cardTitle}>{p.name}</h3>
                <span className={styles.cardBadge}>{p.mission_count} missions</span>
              </div>
              <p className={styles.cardDesc}>{p.description || 'No description provided.'}</p>
              <div className={styles.cardFooter}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  {p.location && <><MapPin size={12} /> {p.location}</>}
                </span>
                <span>Created {new Date(p.created_at * 1000).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {showCreate && (
        <div className={styles.modalOverlay}>
          <div className={styles.modal}>
            <h3>Create New Project</h3>
            <form onSubmit={handleCreate}>
              <div className={styles.formGroup}>
                <label htmlFor="projectName">Project Name *</label>
                <input 
                  id="projectName"
                  autoFocus 
                  required 
                  value={formData.name} 
                  onChange={e => setFormData({...formData, name: e.target.value})} 
                  placeholder="e.g. Hong Kong Operations" 
                />
              </div>
              <div className={styles.formGroup}>
                <label htmlFor="projectLocation">Location</label>
                <input 
                  id="projectLocation"
                  value={formData.location} 
                  onChange={e => setFormData({...formData, location: e.target.value})} 
                  placeholder="e.g. HKG" 
                />
              </div>
              <div className={styles.formGroup}>
                <label htmlFor="projectDescription">Description</label>
                <textarea 
                  id="projectDescription"
                  rows={3} 
                  value={formData.description} 
                  onChange={e => setFormData({...formData, description: e.target.value})} 
                  placeholder="Airport and terminal surveys." 
                />
              </div>
              <div className={styles.modalActions}>
                <button type="button" className={styles.cancelBtn} onClick={() => setShowCreate(false)}>Cancel</button>
                <button type="submit" className={styles.createBtn}>Create</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
