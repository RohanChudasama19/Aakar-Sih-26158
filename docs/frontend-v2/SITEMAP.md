# AAKAR Frontend V2 Sitemap

This sitemap reflects the user journey through the global sidebar and nested workflows.

## 1. Mission Control (Dashboard)
- **Path:** /
- **Purpose:** First-time empty state or returning-user overview. Displays active missions, system readiness, and quick-start actions.

## 2. Projects
- **Path:** /projects
- **Purpose:** Manage the project hierarchy.
- **Nested Views:**
  - Project Listing (Search, Create, Rename, Archive)
  - Project Detail (/projects/:projectId): Shows missions belonging to the specific project.

## 3. New Reconstruction
- **Path:** /new
- **Purpose:** Multi-step wizard to create a new mission.
  - Step 1: Project selection & Mission details
  - Step 2: Upload source inputs (Video, GPS)
  - Step 3: Configure settings (Processing profile)
  - Step 4: Review and submit

## 4. 3D Workspace
- **Path:** /workspace/:jobId
- **Purpose:** The core 3D exploration and measurement interface.
- **Empty State (/workspace):** Mission selector prompt (prevents /workspace/undefined).

## 5. Quality Intelligence
- **Path:** /quality/:jobId
- **Purpose:** Mission-specific scientific reports (Overlap, RMSE, Component fractions, Performance).

## 6. Exports
- **Path:** /exports/:jobId
- **Purpose:** Download verified artifacts (GLB, PLY, JSON).

## 7. Settings
- **Path:** /settings
- **Purpose:** Global application configuration, engine diagnostics, and dependency health.
