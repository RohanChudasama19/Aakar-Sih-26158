import uuid
import time
from typing import Any, Dict

from sqlalchemy import JSON, Float, String, ForeignKey, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
Session = sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(String(2000), default="")
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[float] = mapped_column(Float, default=time.time)
    updated_at: Mapped[float] = mapped_column(Float, default=time.time)
    archived_at: Mapped[float] = mapped_column(Float, nullable=True)

class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(24), default="queued")
    stage: Mapped[str] = mapped_column(String(8), default="")
    progress: Mapped[float] = mapped_column(Float, default=0)
    message: Mapped[str] = mapped_column(String(2000), default="Queued")
    created: Mapped[float] = mapped_column(Float, default=time.time)
    updated: Mapped[float] = mapped_column(Float, default=time.time)
    options: Mapped[dict] = mapped_column(JSON, default=dict)
    report: Mapped[dict] = mapped_column(JSON, default=dict)
    readiness_status: Mapped[str] = mapped_column(String(24), default="pending")
    readiness_score: Mapped[float] = mapped_column(Float, default=0.0)
    readiness_report_path: Mapped[str] = mapped_column(String(255), default="")

def init_db() -> None:
    # Safely migrate SQLite schema
    with engine.begin() as conn:
        # Create projects table
        Base.metadata.create_all(engine)
        
        # Check if project_id exists on jobs
        result = conn.execute(text("PRAGMA table_info(jobs)")).fetchall()
        columns = [row[1] for row in result]
        if "project_id" not in columns:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN project_id VARCHAR(36) REFERENCES projects(id)"))
    
    # Seed legacy project and assign unassociated jobs
    with Session.begin() as s:
        legacy = s.get(Project, "default-legacy-project")
        if not legacy:
            legacy = Project(
                id="default-legacy-project",
                name="Imported / Legacy Missions",
                description="Auto-migrated missions without an assigned project.",
            )
            s.add(legacy)
        
        # Assign unassociated jobs
        s.execute(text("UPDATE jobs SET project_id = 'default-legacy-project' WHERE project_id IS NULL"))

def update(job_id: str, **values: Any) -> None:
    with Session.begin() as s:
        j = s.get(Job, job_id)
        if j is None:
            raise ValueError("Unknown job")
        for k, v in values.items():
            setattr(j, k, v)
        j.updated = time.time()

def serialize(j: Job) -> Dict[str, Any]:
    return {
        k: getattr(j, k)
        for k in (
            "id",
            "project_id",
            "name",
            "status",
            "stage",
            "progress",
            "message",
            "created",
            "updated",
            "options",
            "report",
            "readiness_status",
            "readiness_score",
            "readiness_report_path",
        )
    }

def serialize_project(p: Project) -> Dict[str, Any]:
    return {
        k: getattr(p, k)
        for k in (
            "id",
            "name",
            "description",
            "location",
            "created_at",
            "updated_at",
            "archived_at",
        )
    }
