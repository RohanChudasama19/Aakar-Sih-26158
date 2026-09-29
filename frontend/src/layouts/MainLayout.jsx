import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { 
  Rocket, Map, Box, Activity, ShieldCheck, 
  Database, Download, Settings, Server
} from 'lucide-react';
import styles from './MainLayout.module.css';
import { fetchSystemHealth } from '../api/system';

const MainLayout = () => {
  const navigate = useNavigate();
  const [health, setHealth] = useState(null);

  useEffect(() => {
    fetchSystemHealth().then(setHealth).catch(console.error);
    const id = setInterval(() => fetchSystemHealth().then(setHealth).catch(console.error), 15000);
    return () => clearInterval(id);
  }, []);

  const navItems = [
    { id: '01', icon: Rocket, label: 'Mission Control', to: '/' },
    { id: '02', icon: Map, label: 'New Reconstruction', to: '/new' },
    { id: '03', icon: Database, label: 'Projects', to: '/projects' },
    { id: '04', icon: Box, label: '3D Workspace', to: '/workspace' },
    { id: '05', icon: ShieldCheck, label: 'Quality Intelligence', to: '/quality' },
    { id: '06', icon: Download, label: 'Exports', to: '/exports' },
    { id: '07', icon: Settings, label: 'Settings', to: '/settings' },
  ];

  const isWorkerAvail = health?.queue?.available;

  return (
    <div className={styles.container}>
      <aside className={styles.sidebar}>
        <div className={styles.logoContainer}>
          <div className={styles.logoMark}>
            <img src="/aakar-logo.png" alt="AAKAR Logo" className={styles.logoImg} />
          </div>
          <div className={styles.logoText}>
            <h2>AAKAR</h2>
            <span>SIH26158</span>
          </div>
        </div>

        <nav className={styles.navigation}>
          {navItems.map((item) => (
            <NavLink 
              key={item.id} 
              to={item.to}
              className={({ isActive }) => 
                isActive ? `${styles.navItem} ${styles.active}` : styles.navItem
              }
            >
              <span className={styles.navId}>{item.id}</span>
              <item.icon className={styles.navIcon} size={18} />
              <span className={styles.navLabel}>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className={styles.systemStatus}>
          <div className={styles.statusHeader}>
            <span>System Status</span>
            <div className={styles.statusDot} style={{ backgroundColor: isWorkerAvail ? 'var(--color-success)' : 'var(--color-danger)' }}></div>
          </div>
          <div className={styles.statusDetails}>
            <div className={styles.statusItem}><span>API</span> <span className={styles.statusOk}>ONLINE</span></div>
            <div className={styles.statusItem}><span>Worker</span> <span className={isWorkerAvail ? styles.statusOk : styles.statusError}>{isWorkerAvail ? 'READY' : 'UNAVAILABLE'}</span></div>
            <div className={styles.statusItem}><span>Redis</span> <span className={health?.queue?.message ? styles.statusOk : styles.statusError}>{health?.queue?.message ? 'AVAILABLE' : 'UNKNOWN'}</span></div>
          </div>
        </div>
      </aside>

      <main className={styles.mainContent}>
        <header className={styles.header}>
          <div className={styles.headerLeft}>
            <h1>Mission Control</h1>
            <p>Single-Pass 3D Reconstruction Intelligence</p>
          </div>
          <div className={styles.headerRight}>
            <div className={styles.engineStatus}>
              <div className={styles.statusDot} style={{ backgroundColor: isWorkerAvail ? 'var(--color-success)' : 'var(--color-danger)' }}></div>
              Reconstruction Engine {isWorkerAvail ? 'Online' : 'Offline'}
            </div>
            <button className={styles.newMissionBtn} onClick={() => navigate('/new')}>+ New Reconstruction</button>
          </div>
        </header>

        <div className={styles.workspace}>
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default MainLayout;
