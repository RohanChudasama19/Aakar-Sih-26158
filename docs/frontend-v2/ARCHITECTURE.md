# AAKAR Frontend V2 Architecture

## Overview
AAKAR Frontend V2 is an architectural evolution of the existing React application. The primary goal is to introduce a strict Project -> Mission -> Reconstruction Outputs data hierarchy while preserving the friend-designed dark theme, React visual identity, existing scientific thresholds, and validated reconstruction artifacts.

## Technology Stack
- **Frontend Framework:** React (Vite build system)
- **Routing:** React Router v6
- **Styling:** CSS Modules with plain CSS (preserving existing theme variables)
- **3D Engine:** Three.js (raw engine wrapper via iewer.js, bridging to React via AAKARViewer.jsx)
- **Backend:** FastAPI (Python)
- **Database:** SQLite (via SQLAlchemy)

## Core Architectural Principles
1. **Preservation of Existing Assets:** The UI visual design (sidebar, cards, typography, turquoise accents) is locked. The backend reconstruction pipeline (COLMAP, PatchMatch, Poisson meshing) is completely decoupled and must not be rerun for this integration.
2. **Entity Hierarchy:** Reconstructions (previously standalone "Jobs") are now formally "Missions" that strictly belong to "Projects".
3. **Graceful Empty States:** Mission-specific routes (/workspace, /quality, /exports) must require a selected mission. Global paths that lack a mission ID must present a robust empty state or a selection modal, never routing to /workspace/undefined.
4. **SPA Fallback Integrity:** FastAPI handles SPA history API fallback securely, ensuring missing /api/* and /assets/* requests yield strict 404 JSON/responses, never masked by index.html.

## Component Strategy
- **Layouts:** MainLayout provides the global sidebar and header.
- **Pages:** Top-level route components map directly to the global sidebar navigation.
- **Viewer:** The Three.js canvas remains isolated in iewer.js to prevent React rendering cycle leaks, while AAKARViewer.jsx handles mount/unmount and ResizeObserver integration.

