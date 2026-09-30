# TechScope AI Development Status

Last updated: 2026-09-30

## Product Direction

TechScope is being developed as an evidence-oriented technology intelligence platform. It ingests technology feeds, normalizes articles, extracts readable content, analyzes articles, groups related stories, and exposes authenticated APIs and a dashboard.

## Completed

### Foundation

- Canonical FastAPI API in `api/serve.py`
- Canonical SQLite database at `data/techscope.db`
- Configurable PostgreSQL backend through `DATABASE_URL`
- Schema version tracking through `schema_migrations`
- SQLite/PostgreSQL-compatible storage repositories
- Dockerfile and Docker Compose with PostgreSQL and Redis services
- Pinned dependencies in `requirements.lock`

### Ingestion

- RSS, Atom, and JSON Feed parsing
- Feed registry and feed CRUD
- ETag and Last-Modified conditional requests
- Feed health state: last checked, error, validators
- Per-feed polling interval selection
- Source-specific parsers for Ars Technica, TechCrunch, The Verge, and Wired
- Readability extraction with optional Trafilatura and HTML fallback
- Public-URL SSRF protections
- Article deduplication and canonical URL upserts

### Analysis

- OpenAI/Hugging Face summarization with deterministic fallback
- Keyword extraction with KeyBERT/RAKE/frequency fallback
- Experimental explainable content-quality signals
- Labelled evaluation dataset and evaluator
- TF-IDF story clustering with persisted cluster IDs
- Evidence extraction for attribution sentences and URLs
- Redis-backed ingestion queue with standalone `worker.py`
- Per-user bookmarks and read state
- TF-IDF semantic search endpoint

### API and Security

- API-key compatibility authentication
- First-admin bootstrap endpoint
- Password-hashed users and bearer sessions
- Basic admin/user authorization
- Authenticated dashboard and records API
- Security headers, host validation, CORS restrictions
- Input bounds and rate limiting
- Durable ingestion job records
- Health endpoint

### Verification

- Current test command: `python -m unittest discover -s tests -v`
- Current result: 20 tests passing
- Compilation: passing
- `git diff --check`: passing
- Quality evaluator: 8 examples, 0.375 accuracy, status `experimental`

## Current Implementation Notes

- `POST /api/v1/ingest` creates a durable job.
- When `REDIS_URL` is configured, jobs are pushed to `techscope:jobs` and consumed by `worker.py`.
- Without Redis, local development uses a thread executor fallback.
- PostgreSQL support is wired and represented in Compose, but a live PostgreSQL integration test still needs to be run.
- The quality model must not be described as factuality or source reliability.
- SQL `LIKE` search and TF-IDF semantic search are both available.
- The dashboard is functional but still minimal.

## Remaining Priorities

1. Add richer story timelines and saved searches on top of semantic search.
2. Add claim/evidence graphs and source reputation with independent evaluation data.
3. Expand the labelled quality dataset and add calibration/benchmark reports.
4. Add notifications, webhooks, Slack/Discord/Telegram/Matrix integrations.
5. Add OpenTelemetry, Prometheus metrics, structured logs, CI/CD, security scans, and load tests.
6. Add PWA/mobile reading experience and keyboard/accessibility workflows.
7. Add plugin/adapter SDKs and community source contribution tooling.

## Handoff Commands

```bash
python -m compileall -q .
python -m unittest discover -s tests -v
python -m utils.evaluate_quality
python -m uvicorn api.serve:app --reload --port 8000
python -m uvicorn dashboard.dashboard:app --reload --port 8501
```

## Handoff Rule

Before starting the next priority: read this file, inspect `git status`, run the test command, update the relevant status section after implementation, and record any limitation that was not verified in the current environment.
