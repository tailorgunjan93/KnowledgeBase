"""
Celery application factory.

The Celery app is created from AppSettings so every config value comes from
.env / environment variables — exactly like the FastAPI app.

If ``CELERY_BROKER_URL`` is not set (empty string), the upload endpoint falls
back to FastAPI BackgroundTasks, so no Redis is needed for local dev.
"""
from celery import Celery
from src.core.settings import get_settings


def make_celery() -> Celery:
    s = get_settings()
    app = Celery(
        "synapse_worker",
        broker=s.celery_broker_url or "memory://",   # memory:// is a no-op placeholder
        backend=s.celery_result_backend or "cache+memory://",
        include=["src.worker.tasks.indexing"],
    )
    app.conf.update(
        # Serialisation
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],

        # Reliability
        task_track_started=True,
        task_acks_late=True,           # ack only AFTER task finishes (prevents lost tasks)
        worker_prefetch_multiplier=1,  # one task at a time per worker (memory-safe for ML)

        # Retry / startup
        broker_connection_retry_on_startup=True,

        # Timezone
        timezone="UTC",
        enable_utc=True,
    )
    return app


celery_app = make_celery()
