# AAKAR Frontend V2 Route Map

React Router v6 configuration mapping.

| Route Path | React Component | Layout | Expected Parameters | Description |
|---|---|---|---|---|
| / | Dashboard | MainLayout | None | Mission Control overview |
| /projects | ProjectList | MainLayout | None | Lists all projects |
| /projects/new | ProjectCreate | MainLayout | None | Project creation modal/page |
| /projects/:projectId | ProjectDetail | MainLayout | projectId (UUID) | Specific project overview |
| /projects/:projectId/missions | MissionList | MainLayout | projectId (UUID) | Missions inside a project |
| /new | NewMission | MainLayout | None | Creation wizard |
| /missions/:jobId | MissionDetail | MainLayout | jobId (UUID) | Mission metadata & overview |
| /missions/:jobId/processing | MissionProcessing | MainLayout | jobId (UUID) | Live progress monitoring |
| /workspace | MissionSelector | MainLayout | None | Empty state for workspace |
| /workspace/:jobId | Workspace | MainLayout | jobId (UUID) | 3D Viewer & Tools |
| /quality | MissionSelector | MainLayout | None | Empty state for quality |
| /quality/:jobId | QualityIntelligence | MainLayout | jobId (UUID) | Validation reports |
| /exports | MissionSelector | MainLayout | None | Empty state for exports |
| /exports/:jobId | Exports | MainLayout | jobId (UUID) | Artifact downloads |
| /settings | Settings | MainLayout | None | Global settings |

*Note: Backward compatibility for existing deep links like /workspace/mars_hkairport01_quality is natively preserved via the :jobId param.*
