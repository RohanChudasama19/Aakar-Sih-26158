code = open('app/main.py', encoding='utf-8').read()

project_endpoints = '''
from .db import Project, serialize_project
from pydantic import BaseModel, constr

class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    location: str = ""

class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    location: str | None = None

@app.get("/api/projects")
def list_projects():
    with Session() as s:
        projects = s.query(Project).filter(Project.archived_at == None).all()
        # count missions
        res = []
        for p in projects:
            count = s.query(Job).filter(Job.project_id == p.id).count()
            data = serialize_project(p)
            data["mission_count"] = count
            res.append(data)
        return res

@app.post("/api/projects", status_code=201)
def create_project(data: ProjectCreate):
    if not 1 <= len(data.name.strip()) <= 160:
        raise HTTPException(422, "Project name must be 1-160 characters")
    p = Project(name=data.name.strip(), description=data.description, location=data.location)
    with Session.begin() as s:
        s.add(p)
    return serialize_project(p)

@app.get("/api/projects/{pid}")
def get_project(pid: str):
    with Session() as s:
        p = s.get(Project, pid)
        if not p:
            raise HTTPException(404, "Project not found")
        data = serialize_project(p)
        data["mission_count"] = s.query(Job).filter(Job.project_id == pid).count()
        return data

@app.patch("/api/projects/{pid}")
def update_project(pid: str, data: ProjectUpdate):
    with Session.begin() as s:
        p = s.get(Project, pid)
        if not p:
            raise HTTPException(404, "Project not found")
        if data.name is not None:
            if not 1 <= len(data.name.strip()) <= 160:
                raise HTTPException(422, "Project name must be 1-160 characters")
            p.name = data.name.strip()
        if data.description is not None:
            p.description = data.description
        if data.location is not None:
            p.location = data.location
        p.updated_at = time.time()
        return serialize_project(p)

@app.delete("/api/projects/{pid}")
def archive_project(pid: str):
    with Session.begin() as s:
        p = s.get(Project, pid)
        if not p:
            raise HTTPException(404, "Project not found")
        p.archived_at = time.time()
        p.updated_at = time.time()
        return serialize_project(p)

@app.post("/api/projects/{pid}/restore")
def restore_project(pid: str):
    with Session.begin() as s:
        p = s.get(Project, pid)
        if not p:
            raise HTTPException(404, "Project not found")
        p.archived_at = None
        p.updated_at = time.time()
        return serialize_project(p)

@app.get("/api/projects/{pid}/missions")
def get_project_missions(pid: str):
    with Session() as s:
        p = s.get(Project, pid)
        if not p:
            raise HTTPException(404, "Project not found")
        jobs = s.query(Job).filter(Job.project_id == pid).order_by(Job.created.desc()).all()
        return [serialize(j) for j in jobs]
'''

import re
# Insert just before @app.get("/api/jobs")
code = re.sub(r'(@app\.get\("/api/jobs"\))', project_endpoints + r'\n\n\1', code, count=1)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Injected project endpoints.")
