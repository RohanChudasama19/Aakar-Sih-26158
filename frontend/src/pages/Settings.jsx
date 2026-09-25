import React from 'react';
import { useTheme } from '../context/ThemeContext';
import styles from './Settings.module.css';

const Settings = () => {
  const { theme, setTheme, availableThemes } = useTheme();

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>System Settings</h2>
        <p>Configure interface, reconstruction defaults, and AI model parameters.</p>
      </div>

      <div className={styles.content}>
        <div className={styles.sidebar}>
          <ul className={styles.navList}>
            <li className={styles.active}>Appearance</li>
            <li>Mission Defaults</li>
            <li>AI Models</li>
            <li>Reconstruction Engine</li>
            <li>Hardware & Storage</li>
          </ul>
        </div>

        <div className={styles.mainPanel}>
          <section className={styles.section}>
            <h3>Interface Theme</h3>
            <p className={styles.description}>
              Select the visual identity of the platform. The default Dark Aerospace theme is recommended for extended mission monitoring.
            </p>

            <div className={styles.themeGrid}>
              {availableThemes.map((t) => (
                <div 
                  key={t.id} 
                  className={`${styles.themeCard} ${theme === t.id ? styles.selected : ''}`}
                  onClick={() => setTheme(t.id)}
                >
                  <div className={`${styles.themePreview} ${styles[t.id]}`}>
                    <div className={styles.previewSidebar}></div>
                    <div className={styles.previewMain}>
                      <div className={styles.previewHeader}></div>
                      <div className={styles.previewContent}>
                        <div className={styles.previewCard}></div>
                        <div className={styles.previewCard}></div>
                      </div>
                    </div>
                  </div>
                  <div className={styles.themeInfo}>
                    <span className={styles.themeName}>{t.label}</span>
                    {theme === t.id && <span className={styles.activeBadge}>Active</span>}
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className={styles.section}>
            <h3>Display Preferences</h3>
            <div className={styles.settingRow}>
              <div className={styles.settingInfo}>
                <h4>Telemetry Real-time Updates</h4>
                <p>Refresh rate of the telemetry data streaming from the drone.</p>
              </div>
              <select className={styles.select}>
                <option>High (60 Hz)</option>
                <option>Medium (30 Hz)</option>
                <option>Low (10 Hz)</option>
              </select>
            </div>
            <div className={styles.settingRow}>
              <div className={styles.settingInfo}>
                <h4>3D Viewport Quality</h4>
                <p>Default rendering quality for point clouds and meshes.</p>
              </div>
              <select className={styles.select}>
                <option>Ultra (Gaussian Splatting)</option>
                <option>High (Textured Mesh)</option>
                <option>Draft (Point Cloud)</option>
              </select>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default Settings;
