# AAKAR Frontend V2 Implementation Plan

## Phase 2 Roadmap

### Step 1: Database Migration
1. Implement the SQLite ALTER TABLE script for projects and project_id.
2. Seed the fallback default-legacy-project.
3. Add SQLAlchemy models to pp/db.py.
4. Run DB tests to verify mars_hkairport01_quality remains fully accessible.

### Step 2: Backend API Expansion
1. Implement POST /api/projects, GET /api/projects, GET /api/projects/{pid}.
2. Implement DELETE /api/projects/{pid} and DELETE /api/jobs/{jid}.
3. Update POST /api/jobs to accept an optional project_id payload.

### Step 3: Frontend Route Setup
1. Update App.jsx to match the exact paths defined in ROUTE_MAP.md.
2. Create empty shell components for ProjectList, ProjectDetail, MissionDetail.

### Step 4: Mission Control & Projects UI
1. Build pages/Projects.jsx.
2. Implement project creation modal.
3. Build the Dashboard overview showing active jobs grouped by project.

### Step 5: Mission Wizard Updates
1. Modify NewMission.jsx to inject a "Select Project" dropdown in Step 1.
2. Connect submission payload to updated FastAPI endpoints.

### Step 6: Empty States & Deep Links
1. Implement MissionSelector fallback for direct hits to /workspace, /quality, /exports.
2. Verify deep links (/workspace/mars_hkairport01_quality) bypass the selector.

### Step 7: 3D Exploration Engine (Phase 3 Prep)
1. Add state hooks to AAKARViewer.jsx for cameraMode.
2. Plumb cameraMode into iewer.js and stub out the teardown logic.

## Acceptance Criteria
- All routes render without 404s or white screens.
- Existing historical jobs remain visible and explorable.
- No regression in 3D viewer initialization or scientific quality parsing.
