import time

from sqlalchemy import JSON, Float, String, create_engine
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


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
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


from typing import Any, Dict


def init_db() -> None:
    Base.metadata.create_all(engine)


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
