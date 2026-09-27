import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { MapPin, ArrowLeft, Archive, RefreshCw } from 'lucide-react';
import styles from './Projects.module.css';
import { fetchProject, fetchProjectMissions, archiveProject, restoreProject, updateProject } from '../api/projects';

export default function ProjectDetail() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [missions, setMissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('missions');
  const [showEdit, setShowEdit] = useState(false);
  const [formData, setFormData] = useState({ name: '', description: '', location: '' });

  useEffect(() => {
    loadData();
  }, [projectId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [p, m] = await Promise.all([
        fetchProject(projectId),
        fetchProjectMissions(projectId)
      ]);
      setProject(p);
      setMissions(m);
      setFormData({ name: p.name, description: p.description || '', location: p.location || '' });
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleArchive = async () => {
    if (confirm('Are you sure you want to archive this project? This hides it from the default list but preserves all data.')) {
      try {
        await archiveProject(projectId);
        navigate('/projects');
      } catch (err) {
        alert(err.message || 'Error archiving project');
      }
    }
  };

  const handleRestore = async () => {
    try {
      await restoreProject(projectId);
      loadData();
    } catch (err) {
      alert(err.message || 'Error restoring project');
    }
  };

  const handleEdit = async (e) => {
    e.preventDefault();
    try {
      await updateProject(projectId, formData);
      setShowEdit(false);
      loadData();
    } catch (err) {
      alert(err.message || 'Error updating project');
    }
  };

  if (loading) return <div className={styles.emptyState}>Loading project details...</div>;
  if (!project) return <div className={styles.emptyState}>Project not found.</div>;

  return (
    <div className={styles.container}>
      <button className={styles.cancelBtn} style={{ marginBottom: '16px' }} onClick={() => navigate('/projects')}>
        <ArrowLeft size={16} /> Back to Projects
      </button>

      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>{project.name} {project.archived_at && '(Archived)'}</h1>
          <p className={styles.cardDesc} style={{ marginTop: '8px' }}>{project.description}</p>
          {project.location && (
            <p className={styles.cardDesc} style={{ marginTop: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <MapPin size={14} /> {project.location}
            </p>
          )}
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button className={styles.cancelBtn} onClick={() => setShowEdit(true)}>Edit</button>
          {project.archived_at ? (
            <button className={styles.restoreBtn} onClick={handleRestore}><RefreshCw size={16}/> Restore</button>
          ) : (
            <button className={styles.archiveBtn} onClick={handleArchive}><Archive size={16}/> Archive</button>
          )}
        </div>
      </div>

      <div className={styles.tabs}>
        <div className={`${styles.tab} ${activeTab === 'missions' ? styles.active : ''}`} onClick={() => setActiveTab('missions')}>Missions</div>
        <div className={`${styles.tab} ${activeTab === 'reports' ? styles.active : ''}`} onClick={() => setActiveTab('reports')}>Reports</div>
      </div>

      {activeTab === 'missions' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
             <button className={styles.createBtn} onClick={() => navigate('/new')}>New Mission</button>
          </div>
          {missions.length === 0 ? (
            <div className={styles.emptyState}>
              <h3>No Missions</h3>
              <p>This project has no missions yet.</p>
            </div>
          ) : (
            <div>
              {missions.map(m => (
                <div key={m.id} className={styles.missionRow} onClick={() => navigate(`/missions/${m.id}`)}>
                  <div className={styles.missionInfo}>
                    <h4>{m.name}</h4>
                    <p>ID: {m.id} | Created: {new Date(m.created * 1000).toLocaleString()}</p>
                  </div>
                  <div className={styles.missionStatus}>
                    <span>{m.status.toUpperCase()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'reports' && (
        <div className={styles.emptyState}>
          <h3>Project Reports</h3>
          <p>Aggregated project-level reporting will be available in Phase 3.</p>
        </div>
      )}

      {showEdit && (
        <div className={styles.modalOverlay}>
          <div className={styles.modal}>
            <h3>Edit Project</h3>
            <form onSubmit={handleEdit}>
              <div className={styles.formGroup}>
                <label htmlFor="editProjectName">Project Name *</label>
                <input id="editProjectName" required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
              </div>
              <div className={styles.formGroup}>
                <label htmlFor="editProjectLocation">Location</label>
                <input id="editProjectLocation" value={formData.location} onChange={e => setFormData({...formData, location: e.target.value})} />
              </div>
              <div className={styles.formGroup}>
                <label htmlFor="editProjectDescription">Description</label>
                <textarea id="editProjectDescription" rows={3} value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} />
              </div>
              <div className={styles.modalActions}>
                <button type="button" className={styles.cancelBtn} onClick={() => setShowEdit(false)}>Cancel</button>
                <button type="submit" className={styles.createBtn}>Save</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
