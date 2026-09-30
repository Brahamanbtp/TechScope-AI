import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from storage.job_repo import create_job, update_job
from utils.scheduler import ingest_feeds_once


logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="techscope-job")
QUEUE_NAME = "techscope:jobs"


def run_ingest_job(job_id: str) -> None:
    update_job(job_id, "running")
    try:
        saved = ingest_feeds_once()
        update_job(job_id, "succeeded", {"saved": saved})
    except Exception as exc:
        logger.exception("Ingestion job %s failed", job_id)
        update_job(job_id, "failed", error="Ingestion failed")


def _redis_client():
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return None
    try:
        import redis
        return redis.Redis.from_url(redis_url, decode_responses=True)
    except ImportError:
        return None


def submit_ingest_job() -> dict:
    job_id = str(uuid4())
    job = create_job(job_id, "feed_ingest")
    client = _redis_client()
    if client is not None:
        client.rpush(QUEUE_NAME, job_id)
    else:
        executor.submit(run_ingest_job, job_id)
    return job


def run_worker() -> None:
    client = _redis_client()
    if client is None:
        raise RuntimeError("REDIS_URL and redis package are required for the worker")
    logger.info("Starting TechScope Redis worker")
    while True:
        item = client.blpop(QUEUE_NAME, timeout=30)
        if item:
            _, job_id = item
            run_ingest_job(job_id)