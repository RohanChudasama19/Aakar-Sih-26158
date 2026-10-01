from app.db import Session, Job, Project
with Session() as s:
    legacy = s.get(Project, "default-legacy-project")
    print("Project:", legacy.name)
    mars = s.get(Job, "mars_hkairport01_quality")
    print("MARS Project ID:", mars.project_id)
