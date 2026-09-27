import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import Dashboard from './pages/Dashboard';
import Settings from './pages/Settings';
import Workspace from './pages/Workspace';
import NewMission from './pages/NewMission';
import Exports from './pages/Exports';
import ProjectList from './pages/ProjectList';
import ProjectDetail from './pages/ProjectDetail';
import MissionDetail from './pages/MissionDetail';

import MissionSelector from './pages/MissionSelector';

const Placeholder = ({ title }) => (
  <div style={{ color: 'var(--text-primary)', padding: '24px' }}>
    <h2>{title}</h2>
    <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>This module is currently in development.</p>
  </div>
);

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="new" element={<NewMission />} />
          <Route path="projects" element={<ProjectList />} />
          <Route path="projects/:projectId" element={<ProjectDetail />} />
          
          <Route path="missions/:jobId" element={<MissionDetail />} />
          <Route path="missions/:jobId/processing" element={<MissionDetail />} />
          
          <Route path="workspace" element={<MissionSelector toolName="3D Workspace" toolRoute="workspace" />} />
          <Route path="workspace/:jobId" element={<Workspace />} />
          
          <Route path="quality" element={<MissionSelector toolName="Quality Intelligence" toolRoute="quality" />} />
          <Route path="quality/:jobId" element={<Placeholder title="Quality Intelligence" />} />
          
          <Route path="exports" element={<MissionSelector toolName="Exports" toolRoute="exports" />} />
          <Route path="exports/:jobId" element={<Exports />} />
          
          <Route path="analytics" element={<Placeholder title="Flight Analytics" />} />
          <Route path="models" element={<Placeholder title="AI Models" />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
