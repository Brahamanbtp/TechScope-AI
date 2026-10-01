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
- User-owned saved searches
- Chronological story timelines per cluster
- Candidate claims linked to extracted evidence
- Transparent source coverage/quality aggregates
- Webhook subscriptions and event delivery
- Prometheus-style request metrics endpoint
- PWA manifest/service worker shell
- CI workflow and Python tooling configuration
- Structured JSON logging and request metrics
- Load-test script and CI security scan steps
- Source adapter protocol, registry, documentation, and contract test
- Human quality review submission and calibration report workflow
- Slack, Discord, Telegram, and Matrix payload adapters
- Provider-aware webhook subscriptions with adapter selection
- Webhook delivery retry/dead-letter persistence
- Optional OpenTelemetry instrumentation and Prometheus counters
- PWA keyboard navigation and accessible focus workflow
- Publishable SDK scaffold in `sdk/`

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
- Current result: 24 tests passing
- Compilation: passing
- `git diff --check`: passing
- Quality evaluator: 30 examples, per-class metrics, calibration bins, Brier score, status `experimental`

## Current Implementation Notes

- `POST /api/v1/ingest` creates a durable job.
- When `REDIS_URL` is configured, jobs are pushed to `techscope:jobs` and consumed by `worker.py`.
- Without Redis, local development uses a thread executor fallback.
- PostgreSQL support is wired and represented in Compose, but a live PostgreSQL integration test still needs to be run.
- The quality model must not be described as factuality or source reliability.
- SQL `LIKE` search and TF-IDF semantic search are both available.
- The dashboard is functional but still minimal.
- Webhook subscriptions, provider payloads, retries/dead-letter delivery, PWA shell, CI, tooling, structured logs, and request metrics are implemented; full distributed tracing remains.
- `scripts/benchmark_quality.py` writes `data/quality_benchmark.json`.
- `scripts/calibrate_quality.py` writes human-review calibration data when production reviews exist.
- `scripts/import_public_benchmark.py` imports public FEVER factuality data into a separate task dataset; it is not mixed with editorial-quality labels.
- FEVER repository metadata was reachable, but its official data download URL was not verified in this environment; the importer therefore requires an explicit URL instead of using a false default.

## Remaining Priorities

1. Collect enough independently labelled production data to calibrate the quality model.
2. Add integration-specific credentials and delivery retry queues for notification services.
3. Add distributed OpenTelemetry exporters and production metrics dashboards.
4. Expand the PWA into complete offline article caching and mobile navigation.
5. Publish the SDK to a package registry with release automation.

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
