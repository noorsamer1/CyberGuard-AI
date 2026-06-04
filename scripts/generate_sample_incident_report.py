#!/usr/bin/env python3
"""Generate a sample incident PDF demonstrating richer report sections."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings  # noqa: E402
from app.core.database import Base  # noqa: E402
from app.models.enums import IncidentStatus  # noqa: E402
from app.models.incident import Incident  # noqa: E402
from app.services.event_service import EventService  # noqa: E402
from app.services.incident_report_context import (  # noqa: E402
    build_incident_report_context,
    context_to_dict,
)
from app.services.range_service import logs_to_events  # noqa: E402
from app.services.report_service import build_incident_pdf, ensure_reports_dir  # noqa: E402
from tests.fixtures.range_logs import brute_force_logs  # noqa: E402

import app.models  # noqa: F401, E402


def _sqlite_session():
    """Use an isolated SQLite DB so the script runs without Docker/Postgres."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return session_factory()


def main() -> None:
    settings.ai_detection_enabled = False
    settings.correlation_enabled = False
    settings.reports_dir = str(ROOT / "data" / "reports")

    db = _sqlite_session()
    try:
        service = EventService()
        _, alerts = service.ingest_batch(db, logs_to_events(brute_force_logs()))
        if not alerts:
            raise RuntimeError("No alerts produced from brute-force sample logs.")

        incident = db.get(Incident, alerts[0].incident_id)
        if incident is None:
            raise RuntimeError("Incident was not created for sample alert.")

        incident.ai_summary = (
            "Repeated authentication failures against the local range target "
            "culminated in a successful login after multiple attempts."
        )
        incident.analyst_notes = (
            "Root cause: Intentional brute-force simulation against disposable "
            "/login endpoint.\n\n"
            "Impact: Demonstrates detection of credential stuffing patterns "
            "in lab telemetry only."
        )
        incident.remediation = (
            "P0: Block source IP at range edge.\n"
            "P1: Reset disposable range credentials.\n"
            "P2: Review detection thresholds for production auth logs."
        )
        incident.status = IncidentStatus.investigating
        db.commit()
        db.refresh(incident)

        reports_dir = ensure_reports_dir()
        pdf_path = reports_dir / "sample_incident_report_v2.pdf"
        build_incident_pdf(incident, pdf_path, db=db)

        ctx = build_incident_report_context(db, incident)
        summary_md = reports_dir / "sample_incident_report_sections.md"
        summary_md.write_text(
            "\n".join(
                [
                    "# Sample Incident Report Sections",
                    "",
                    f"- PDF: `{pdf_path.name}`",
                    f"- Incident ID: {incident.id}",
                    "",
                    "## Deterministic sections",
                    "- Incident status and metrics (status, MTTA, MTTR, event count)",
                    "- Event severity breakdown",
                    "- Affected source IPs and destinations",
                    "- Correlation summary (alerts, correlated events, rule families)",
                    "- Attack timeline table",
                    "",
                    "## AI narrative (advisory)",
                    "- Executive summary",
                    "- Analysis notes (root cause, impact)",
                    "- Prioritized remediation",
                    "",
                    "## Context snapshot",
                    "```json",
                    json.dumps(context_to_dict(ctx), indent=2),
                    "```",
                ]
            ),
            encoding="utf-8",
        )
        print(f"Wrote {pdf_path}")
        print(f"Wrote {summary_md}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
