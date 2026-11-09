from celery import Celery

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery(
    "rook",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.update(task_serializer="json", accept_content=["json"], result_serializer="json")


@celery_app.task(name="rook.health_probe")
def health_probe() -> dict[str, str]:
    return {"status": "ok", "worker": "rook-celery"}
