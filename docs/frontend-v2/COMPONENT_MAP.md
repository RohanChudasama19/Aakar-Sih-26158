# AeroRecon Frontend V2 Component Map

## Core Layouts
- layouts/MainLayout.jsx
  - Provides the global sidebar, system status ticker, and top header block.

## Top-Level Pages
- pages/Dashboard.jsx (Mission Control)
- pages/Projects/ProjectList.jsx (New)
- pages/Projects/ProjectDetail.jsx (New)
- pages/NewMission.jsx (Multi-step upload and configuration)
- pages/MissionDetail.jsx (New - Mission overview)
- pages/Workspace.jsx (3D environment wrapper)
- pages/QualityIntelligence.jsx (New - Deep metric visualization)
- pages/Exports.jsx (Artifact management)
- pages/Settings.jsx (Global config)

## Shared UI Components
- components/ui/MissionSelector.jsx (New - Empty state resolution modal)
- components/ui/Button.jsx (To unify action buttons)
- components/ui/Card.jsx (To unify panel styling)
- components/ui/StatusBadge.jsx (Pipeline status indicators)

## 3D Viewer Architecture
- components/viewer/AeroReconViewer.jsx
  - React lifecycle bridge. Handles container refs, mount/dismount, and ResizeObserver.
- iewer/viewer.js
  - Pure JavaScript Three.js implementation. Handles scene graph, loaders (GLTFLoader), camera controls, and raycasting.
