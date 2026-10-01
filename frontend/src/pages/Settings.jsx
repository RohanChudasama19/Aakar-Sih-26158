import React, { useState, useEffect } from 'react';
import { useTheme } from '../context/ThemeContext';
import { Settings as SettingsIcon, Monitor, Server, Cpu, HardDrive, ShieldAlert, CheckCircle, XCircle } from 'lucide-react';
import styles from './Settings.module.css'; // Existing styles

const Settings = () => {
  const { theme, setTheme, availableThemes } = useTheme();
  const [activeTab, setActiveTab] = useState('appearance');
  
  const [health, setHealth] = useState(null);
  const [sysInfo, setSysInfo] = useState(null);
  const [defaults, setDefaults] = useState({ profile: 'QUALITY', frames: 'AUTO' });

  useEffect(() => {
    // Load persisted processing defaults from localStorage
    const savedDefaults = localStorage.getItem('aakar_defaults');
    if (savedDefaults) {
      try { setDefaults(JSON.parse(savedDefaults)); } catch(e){}
    }
    
    // Fetch system info and health
    fetch('/api/health').then(r => r.json()).then(setHealth).catch(console.error);
    fetch('/api/system/info').then(r => r.json()).then(setSysInfo).catch(console.error);
  }, []);
  
  const saveDefaults = (key, val) => {
    const newDefaults = { ...defaults, [key]: val };
    setDefaults(newDefaults);
    localStorage.setItem('aakar_defaults', JSON.stringify(newDefaults));
  };

  const formatBytes = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024, sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const renderTab = () => {
    if (activeTab === 'appearance') {
      return (
        <section className={styles.section}>
          <h3>Interface Theme</h3>
          <p className={styles.description}>Select the visual identity of the platform.</p>
          <div className={styles.themeGrid}>
            {availableThemes.map((t) => (
              <div 
                key={t.id} 
                className={`${styles.themeCard} ${theme === t.id ? styles.selected : ''}`}
                onClick={() => setTheme(t.id)}
              >
                <div className={styles.themeInfo}>
                  <span className={styles.themeName}>{t.label}</span>
                  {theme === t.id && <span className={styles.activeBadge}>Active</span>}
                </div>
              </div>
            ))}
          </div>
        </section>
      );
    }
    
    if (activeTab === 'defaults') {
      return (
        <section className={styles.section}>
          <h3>Processing Defaults</h3>
          <p className={styles.description}>Configure default values for new reconstructions.</p>
          <div className={styles.settingRow}>
            <div className={styles.settingInfo}>
              <h4>Default Processing Profile</h4>
              <p>Performance vs Quality tradeoff.</p>
            </div>
            <select className={styles.select} value={defaults.profile} onChange={e => saveDefaults('profile', e.target.value)}>
              <option value="FAST">FAST</option>
              <option value="BALANCED">BALANCED</option>
              <option value="QUALITY">QUALITY</option>
            </select>
          </div>
        </section>
      );
    }

    if (activeTab === 'engine') {
      return (
        <section className={styles.section}>
          <h3>Reconstruction Engine</h3>
          <p className={styles.description}>Diagnostics and capability detection.</p>
          
          <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <li style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>API Health</span>
              {health?.status === 'ok' ? <span style={{ color: 'var(--color-success)', display: 'flex', alignItems: 'center', gap: '4px' }}><CheckCircle size={14}/> Online</span> : <span style={{ color: 'var(--color-danger)' }}><XCircle size={14}/> Offline</span>}
            </li>
            <li style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Worker Queue Status</span>
              <span>{health?.queue?.status || 'Unknown'} (Workers: {health?.queue?.workers_online})</span>
            </li>
            <li style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>COLMAP Detected</span>
              {health?.capabilities?.colmap ? <span style={{ color: 'var(--color-success)' }}>Yes ({sysInfo?.colmap_path})</span> : <span style={{ color: 'var(--color-danger)' }}>Missing (CPU Fallback likely)</span>}
            </li>
            <li style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Semantic Segmentation</span>
              {health?.capabilities?.segmentation ? <span style={{ color: 'var(--color-success)' }}>Available</span> : <span style={{ color: 'var(--color-warning)' }}>Disabled (Heuristic fallback)</span>}
            </li>
            <li style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>FBX Export</span>
              {health?.capabilities?.fbx ? <span style={{ color: 'var(--color-success)' }}>Available</span> : <span style={{ color: 'var(--color-warning)' }}>Unavailable (Blender missing)</span>}
            </li>
          </ul>
        </section>
      );
    }

    if (activeTab === 'storage') {
      return (
        <section className={styles.section}>
          <h3>Hardware & Storage</h3>
          <p className={styles.description}>Server resource utilization.</p>
          
          <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <li style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Artifact Directory</span>
              <span style={{ fontFamily: 'monospace' }}>{sysInfo?.data_dir || 'Loading...'}</span>
            </li>
            <li style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Storage Used</span>
              <span>{formatBytes(sysInfo?.disk_used)} / {formatBytes(sysInfo?.disk_total)}</span>
            </li>
            <li style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Storage Free</span>
              <span style={{ color: sysInfo?.disk_free < 10*1024*1024*1024 ? 'var(--color-warning)' : 'var(--text-primary)' }}>{formatBytes(sysInfo?.disk_free)}</span>
            </li>
            <li style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>CPU Usage</span>
              <span>{sysInfo?.cpu_percent ?? 0}%</span>
            </li>
            <li style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Memory Usage</span>
              <span>{sysInfo?.mem_percent ?? 0}%</span>
            </li>
          </ul>
        </section>
      );
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><SettingsIcon size={24} color="var(--accent-primary)"/> System Settings</h2>
        <p>Configure interface, reconstruction defaults, and diagnostic telemetry.</p>
      </div>

      <div className={styles.content}>
        <div className={styles.sidebar}>
          <ul className={styles.navList}>
            <li className={activeTab === 'appearance' ? styles.active : ''} onClick={() => setActiveTab('appearance')}><Monitor size={14}/> Appearance</li>
            <li className={activeTab === 'defaults' ? styles.active : ''} onClick={() => setActiveTab('defaults')}><SettingsIcon size={14}/> Processing Defaults</li>
            <li className={activeTab === 'engine' ? styles.active : ''} onClick={() => setActiveTab('engine')}><Cpu size={14}/> Reconstruction Engine</li>
            <li className={activeTab === 'storage' ? styles.active : ''} onClick={() => setActiveTab('storage')}><HardDrive size={14}/> Hardware & Storage</li>
          </ul>
        </div>

        <div className={styles.mainPanel}>
          {renderTab()}
        </div>
      </div>
    </div>
  );
};

export default Settings;
