from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    params: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    stats: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    sources: Mapped[list["Source"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    challenges: Mapped[list["Challenge"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), ForeignKey("runs.id"))
    url: Mapped[str] = mapped_column(Text)
    source_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    published_at: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    credibility: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    html_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    text_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    run: Mapped[Run] = relationship(back_populates="sources")


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), ForeignKey("runs.id"))
    title: Mapped[str] = mapped_column(String(256))
    summary: Mapped[str] = mapped_column(Text)
    challenge_type: Mapped[str] = mapped_column(String(64))
    impact_area: Mapped[list[str]] = mapped_column(JSON)
    severity: Mapped[str] = mapped_column(String(16))
    time_horizon: Mapped[str] = mapped_column(String(16))
    uk_relevance: Mapped[str] = mapped_column(String(16))
    eu_relevance: Mapped[str] = mapped_column(String(16))
    affected_sectors: Mapped[list[str]] = mapped_column(JSON)
    evidence: Mapped[list[dict]] = mapped_column(JSON)
    confidence: Mapped[float] = mapped_column(Float)
    dedupe_key: Mapped[str] = mapped_column(String(128))

    run: Mapped[Run] = relationship(back_populates="challenges")


engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
