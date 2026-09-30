import logging
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from storage.job_repo import create_job, update_job
from utils.scheduler import ingest_feeds_once


logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="techscope-job")


def _run_ingest(job_id: str) -> None:
    update_job(job_id, "running")
    try:
        saved = ingest_feeds_once()
        update_job(job_id, "succeeded", {"saved": saved})
    except Exception as exc:
        logger.exception("Ingestion job %s failed", job_id)
        update_job(job_id, "failed", error="Ingestion failed")


def submit_ingest_job() -> dict:
    job_id = str(uuid4())
    job = create_job(job_id, "feed_ingest")
    executor.submit(_run_ingest, job_id)
    return job