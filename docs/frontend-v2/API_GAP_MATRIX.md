# AAKAR Frontend V2 API Gap Matrix

| Required Capability | Frontend Route Context | Backend API Endpoint | Status | Notes |
|---|---|---|---|---|
| Project Creation | /projects/new | POST /api/projects | MISSING | Requires DB schema update |
| Project Listing | /projects | GET /api/projects | MISSING | |
| Project Detail | /projects/:projectId | GET /api/projects/{pid} | MISSING | |
| Project Update | /projects/:projectId | PUT /api/projects/{pid} | MISSING | Rename/Archive |
| Project Deletion | /projects/:projectId | DELETE /api/projects/{pid} | MISSING | Needs cascade/orphan logic |
| Mission Listing | / | GET /api/jobs | EXISTS_AND_WORKS | |
| Mission Detail | /missions/:jobId | GET /api/jobs/{jid} | EXISTS_AND_WORKS | |
| Mission Creation | /new | POST /api/jobs | PARTIALLY_IMPLEMENTED | Endpoint exists but lacks project_id association |
| Mission Deletion | Various | DELETE /api/jobs/{jid} | MISSING | Important for disk management |
| Mission Status/Events | /missions/:jobId/processing | GET /api/jobs/{jid}/events | EXISTS_AND_WORKS | SSE event stream functional |
| Representations | /workspace/:jobId | GET /api/jobs/{jid}/representations | EXISTS_AND_WORKS | Fixed in previous patch |
| Exports / Artifacts | /exports/:jobId | GET /api/jobs/{jid}/files/{path} | EXISTS_AND_WORKS | |
| System Health | /, Global | GET /api/health | EXISTS_AND_WORKS | Powers the sidebar status |
| Settings Persistence | /settings | GET/PUT /api/settings | MISSING | Settings are currently UI-only |
