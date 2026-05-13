from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "cyberguard",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    imports=("app.tasks.ai_tasks", "app.tasks.report_tasks"),
    beat_schedule={
        "run-due-report-schedules": {
            "task": "reports.run_due_schedules",
            "schedule": 900.0,
        },
    },
)
