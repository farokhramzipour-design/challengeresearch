from __future__ import annotations

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.db import Challenge, Run, Source, get_session, init_db
from app.models.schemas import OutputSchema, RunConfig, RunCreateResponse, RunStatus
from app.services.cache import run_dir
from app.services.pipeline import run_pipeline
from app.services.report import to_markdown

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trade-challenges")

app = FastAPI(title="Trade Challenges Research Agent")


@app.on_event("startup")
def on_startup() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    init_db()


def _save_output(run_id: str, output: Dict) -> None:
    root = run_dir(run_id)
    (root / "output.json").write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
    (root / "report.md").write_text(to_markdown(output), encoding="utf-8")


def _store_output(db: Session, run_id: str, output: OutputSchema, sources: list[dict]) -> None:
    for src in sources:
        db.add(
            Source(
                run_id=run_id,
                url=src.get("url"),
                source_name=src.get("source_name"),
                published_at=src.get("published_at"),
                credibility=src.get("credibility"),
                html_path=src.get("html_path"),
                text_path=src.get("text_path"),
            )
        )

    for item in output.items:
        evidence_json = [ev.model_dump(mode="json") for ev in item.evidence]
        db.add(
            Challenge(
                run_id=run_id,
                title=item.title,
                summary=item.summary,
                challenge_type=item.challenge_type,
                impact_area=item.impact_area,
                severity=item.severity,
                time_horizon=item.time_horizon,
                uk_relevance=item.uk_relevance,
                eu_relevance=item.eu_relevance,
                affected_sectors=item.affected_sectors,
                evidence=evidence_json,
                confidence=item.confidence,
                dedupe_key=item.dedupe_key,
            )
        )
    db.commit()


def _run_job(run_id: str, params: Dict) -> None:
    from app.models.db import SessionLocal

    db = SessionLocal()
    try:
        run = db.get(Run, run_id)
        if not run:
            return
        run.status = "running"
        db.commit()

        output, sources = run_pipeline(run_id, params)
        run.stats = output.stats
        run.status = "completed"
        db.commit()

        _store_output(db, run_id, output, sources)
        _save_output(run_id, output.model_dump(mode="json"))
    except Exception as exc:
        run = db.get(Run, run_id)
        if run:
            run.status = "failed"
            run.error = str(exc)
            db.commit()
        logger.error("Run %s failed: %s", run_id, exc)
        logger.error(traceback.format_exc())
    finally:
        db.close()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/runs", response_model=RunCreateResponse)
def create_run(config: RunConfig, background_tasks: BackgroundTasks, db: Session = Depends(get_session)):
    run_id = datetime.utcnow().isoformat()
    run = Run(
        id=run_id,
        created_at=datetime.utcnow(),
        status="queued",
        params=config.model_dump(),
        stats={},
    )
    db.add(run)
    db.commit()

    background_tasks.add_task(_run_job, run_id, config.model_dump())
    return RunCreateResponse(run_id=run_id, status="queued")


@app.get("/runs/{run_id}", response_model=RunStatus)
def get_run(run_id: str, db: Session = Depends(get_session)):
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunStatus(run_id=run.id, status=run.status, created_at=run.created_at, stats=run.stats, error=run.error)


@app.get("/runs/{run_id}/challenges", response_model=OutputSchema)
def get_challenges(run_id: str, db: Session = Depends(get_session)):
    root = run_dir(run_id)
    output_path = root / "output.json"
    if output_path.exists():
        data = json.loads(output_path.read_text(encoding="utf-8"))
        return OutputSchema.model_validate(data)

    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    items = db.query(Challenge).filter(Challenge.run_id == run_id).all()
    output = {
        "run_id": run_id,
        "scope": {"regions": ["UK", "EU"], "topic": "global trade challenges", "languages": ["en"]},
        "items": [
            {
                "title": item.title,
                "summary": item.summary,
                "challenge_type": item.challenge_type,
                "impact_area": item.impact_area,
                "severity": item.severity,
                "time_horizon": item.time_horizon,
                "uk_relevance": item.uk_relevance,
                "eu_relevance": item.eu_relevance,
                "affected_sectors": item.affected_sectors,
                "evidence": item.evidence,
                "confidence": item.confidence,
                "dedupe_key": item.dedupe_key,
            }
            for item in items
        ],
        "stats": run.stats or {},
    }
    return OutputSchema.model_validate(output)


@app.get("/runs/success/challenges")
def list_success_challenges(request: Request, db: Session = Depends(get_session)) -> Dict[str, list[dict]]:
    runs = db.query(Run).filter(Run.status == "completed").all()
    base = str(request.base_url).rstrip("/")
    return {
        "items": [
            {"run_id": run.id, "url": f"{base}/runs/{run.id}/challenges"} for run in runs
        ]
    }
