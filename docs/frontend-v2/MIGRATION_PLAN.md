# AeroRecon Frontend V2 Project Data Model

## SQLite Schema Additions

### 1. projects Table
`sql
CREATE TABLE projects (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(160) NOT NULL,
    description VARCHAR(2000) DEFAULT '',
    location VARCHAR(255),
    created_at FLOAT NOT NULL,
    updated_at FLOAT NOT NULL,
    archived_at FLOAT
);
`

### 2. jobs Table (Updates)
`sql
ALTER TABLE jobs ADD COLUMN project_id VARCHAR(36) REFERENCES projects(id);
`

## SQLAlchemy Models (app/db.py)

`python
class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(String(2000), default="")
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[float] = mapped_column(Float, default=time.time)
    updated_at: Mapped[float] = mapped_column(Float, default=time.time)
    archived_at: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Optional relationship mapping
    # jobs = relationship("Job", back_populates="project")

class Job(Base):
    # Existing fields...
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=True)
`
"@
Set-Content docs/frontend-v2/PROJECT_DATA_MODEL.md 

 = @"
# AeroRecon Frontend V2 Migration Plan

## Objective
Safely introduce the projects table and the project_id foreign key on the jobs table without losing or altering any existing jobs, reports, or file artifacts (specifically preserving the validated MARS and Colorado reconstructions).

## Database Migration Strategy
We will perform a safe, automated upgrade script at startup or via a standalone CLI migration tool. We will **never** reset the SQLite database.

1. **Schema Evolution:**
   - Execute CREATE TABLE IF NOT EXISTS projects ...
   - Use SQLite ALTER TABLE to add project_id to the jobs table. (SQLite supports ADD COLUMN natively since 3.1.0).
   
2. **Data Seeding (Backward Compatibility):**
   - Create a single "Legacy Missions" project (e.g., ID default-legacy-project).
   - Run UPDATE jobs SET project_id = 'default-legacy-project' WHERE project_id IS NULL;
   - This explicitly links the existing mars_hkairport01_quality, 95f51b12... (Colorado), and light 38 jobs to a browsable project.

3. **File System Preservation:**
   - No files will be moved. The data/{jobId} folder structure remains identical. Projects act purely as a database-level logical grouping. Artifact resolution will not break.

4. **Rollback Strategy:**
   - Before applying the schema migration, physically copy pp.db to pp.db.bak_{timestamp}.
   - If the backend fails to start, the script will restore the .bak file and exit.
