from celery import Celery


def make_celery() -> Celery:
    try:
        from app.core.config import settings
        broker = getattr(settings, "REDIS_URL", None)
    except Exception:
        broker = None

    if not broker:
        # No Redis configured — return a dummy app that won't actually run tasks
        import logging
        logging.getLogger(__name__).warning(
            "REDIS_URL not set. Celery tasks are defined but will not run."
        )

    app = Celery(
        "movewise",
        broker=broker or "memory://",
        backend=broker or "cache+memory://",
        include=["app.tasks.fbi_tasks", "app.tasks.analysis_tasks"],
    )
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        broker_connection_retry_on_startup=True,
    )
    return app


celery_app = make_celery()
