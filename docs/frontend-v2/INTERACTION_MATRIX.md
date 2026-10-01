# AAKAR Frontend V2 Interaction Matrix

| Control Name | Source Component | Expected Action | Required API | State Behaviors |
|---|---|---|---|---|
| New Reconstruction | MainLayout, Dashboard | Navigates to /new wizard | None | Active route highlight |
| Sidebar Items | MainLayout | Navigate to primary views | None | Active route styling; empty states trigger modals |
| Submit Job | NewMission | Uploads inputs & config, spawns background task | POST /api/jobs | **Loading:** Upload progress bar. **Success:** Redirect to /missions/:jobId/processing. **Error:** Toast notification. |
| Layer Toggle | Workspace | Switches 3D active layer (Textured/Mesh/Dense) | None | Highlight active button; Viewer unloads/loads geometry |
| Measurement Tools | Workspace | Activates Raycaster logic in Viewer | None | **Active:** Tool highlighted, disables Orbit. |
| Cancel Job | MissionProcessing (New) | Interrupts active Celery worker | POST /api/jobs/{jid}/cancel | **Loading:** Spinner. **Success:** Job marked cancelled. |
| Download Artifact | Exports | Triggers browser file download | GET /api/jobs/{jid}/download | **Disabled:** If artifact missing (epresentations.available === false). |
| Create Project | ProjectList (New) | Creates new project grouping | POST /api/projects | **Empty:** "No projects yet." **Loading:** Modal spinner. |
| Delete Project | ProjectDetail (New) | Removes project & cascades | DELETE /api/projects/{pid} | Requires typing project name to confirm. |

*Note: The existing "Dead Buttons" (e.g. placeholder routes for Analytics/Models) have been identified. They will either be fully implemented or hidden in Phase 2 to prevent decorative UI.*
