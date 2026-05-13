"""
Create a demo user and a strong SOC demo dataset. Run inside backend container / venv:

  PYTHONPATH=. python scripts/seed_demo.py

Requires DATABASE_URL and running PostgreSQL.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.services.event_service import EventService
from app.services.synthetic_service import generate_strong_demo_events, strong_demo_legend


def main() -> None:
    db = SessionLocal()
    try:
        email = "analyst@cyberguard.demo"
        if not db.query(User).filter(User.email == email).first():
            u = User(
                name="Demo Analyst",
                email=email,
                password_hash=hash_password("CyberGuardDemo!1"),
            )
            db.add(u)
            db.commit()
            print(f"Created user {email} / CyberGuardDemo!1")
        else:
            print(f"User {email} already exists")

        svc = EventService()
        items = generate_strong_demo_events()
        svc.ingest_batch(db, items)
        print(f"Ingested {len(items)} events (strong demo scenario, chronological).")
        print()
        print(strong_demo_legend())
        print("Open Alerts / Incidents / Dashboard to review.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
