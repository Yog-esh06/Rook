import asyncio

from app.celery_app import celery_app
from app.services.release_service import run_release


@celery_app.task(name="rook.run_release")
def run_release_task(release_id: str, sample_count: int | None = None) -> None:
    asyncio.run(run_release(release_id, sample_count=sample_count))
