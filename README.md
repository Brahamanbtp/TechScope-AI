# TechScope AI

TechScope AI is a FastAPI application for analyzing technology articles. It
stores normalized articles in SQLite and provides optional summarization,
keyword extraction, and explainable content-quality scoring.

## Current Features

- FastAPI analysis endpoints
- Environment-based API key authentication
- Canonical SQLite storage at `data/techscope.db`
- HTML dashboard served by FastAPI
- Optional OpenAI and Hugging Face summarization
- Semantic duplicate detection when Sentence Transformers is installed
- Deterministic fallbacks for local development

## Project Structure

```text
api/serve.py              Canonical FastAPI application
api/auth.py               API key verification
dashboard/dashboard.py   HTML dashboard server
storage/schema.py         Canonical database schema and article writer
utils/                    Analysis and ingestion helpers
sources/                  Source-specific scrapers
data/techscope.db         SQLite database created on startup
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `TECHSCOPE_API_KEY` in `.env` to a long random value. The database schema
is created automatically when the application starts. If the old checked-in
database is invalid, it is moved to an ignored backup file and recreated.

## Run the API

```bash
python -m uvicorn api.serve:app --reload --host 0.0.0.0 --port 8000
```

Endpoints:

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/` | Service status |
| GET | `/articles` | Paginated stored articles; requires `x-api-key` |
| POST | `/summarize` | Summarize text; requires `x-api-key` |
| POST | `/credibility` | Return explainable quality signals; requires `x-api-key` |
| POST | `/keywords` | Extract keywords; requires `x-api-key` |
| POST | `/analyze` | Fetch and analyze a public article URL; requires `x-api-key` |
| GET | `/healthz` | Liveness check |
| POST | `/api/v1/auth/bootstrap` | Create the first admin user once |
| POST | `/api/v1/auth/login` | Create an expiring bearer session |
| GET | `/api/v1/feeds` | List configured feeds; requires `x-api-key` |
| GET | `/api/v1/feeds/health` | Feed freshness and error state; requires `x-api-key` |
| POST | `/api/v1/feeds` | Register a feed; requires `x-api-key` |
| DELETE | `/api/v1/feeds/{id}` | Remove a feed; requires `x-api-key` |
| POST | `/api/v1/ingest` | Queue feed ingestion; requires `x-api-key` |
| GET | `/api/v1/jobs/{job_id}` | Read ingestion job status; requires `x-api-key` |
| GET | `/api/v1/articles/{id}` | Retrieve one article; requires `x-api-key` |
| GET | `/api/v1/me/bookmarks` | List current user bookmarks |
| POST | `/api/v1/articles/{id}/bookmark` | Bookmark an article |
| DELETE | `/api/v1/articles/{id}/bookmark` | Remove a bookmark |
| POST | `/api/v1/articles/{id}/read` | Mark an article read |
| GET | `/api/v1/clusters` | List story clusters; requires `x-api-key` |
| GET | `/api/v1/clusters/{id}/timeline` | Chronological story timeline |
| GET | `/api/v1/articles/{id}/claims` | Candidate claims linked to evidence |
| POST | `/api/v1/articles/{id}/review` | Submit an authenticated human quality review |
| GET | `/api/v1/articles/{id}/reviews` | View reviews; admin only |
| POST | `/api/v1/reputation/rebuild` | Rebuild source signal aggregates; admin only |
| GET | `/api/v1/reputation` | View source signal aggregates |
| GET | `/api/v1/me/webhooks` | List user webhook subscriptions |
| POST | `/api/v1/me/webhooks` | Create a webhook subscription |
| DELETE | `/api/v1/me/webhooks/{id}` | Disable a webhook subscription |
| GET | `/metrics` | Prometheus-style request counters |
| POST | `/api/v1/clusters/rebuild` | Rebuild TF-IDF story clusters; admin only |
| GET | `/api/v1/search` | Ranked TF-IDF semantic article search |
| GET | `/api/v1/me/searches` | List saved searches |
| POST | `/api/v1/me/searches` | Save a search |
| DELETE | `/api/v1/me/searches/{id}` | Delete a saved search |

Analysis requests must contain between 100 and 100,000 characters in `text`.
URL analysis accepts only public HTTP(S) URLs, does not follow redirects, limits
responses to 2 MB, and is rate-limited per client address.
Article reads accept `limit` values from 1 to 100 and a non-negative `offset`.
API errors return generic client-safe messages while detailed failures are
written to server logs.
Article browsing also supports `search`, exact `source`, and `min_quality`
filters, for example `/articles?search=quantum&min_quality=0.6`.

## Run the Dashboard

```bash
python -m uvicorn dashboard.dashboard:app --reload --port 8501
```

The dashboard reads the same `articles` table as the API and requires the
`x-api-key` header. Redis is used for distributed analysis rate limiting when
`REDIS_URL` is configured; local development falls back to an in-process limit.

## Configuration

See `.env.example` for supported settings:

- `TECHSCOPE_API_KEY`
- `TECHSCOPE_BOOTSTRAP_SECRET`
- `TECHSCOPE_CORS_ORIGINS`
- `TECHSCOPE_ALLOWED_HOSTS`
- `USE_OPENAI`
- `OPENAI_API_KEY`

AI models are loaded lazily. Without optional model packages or a model cache,
the application uses extractive summarization, frequency-based keywords, and
exact-text duplicate detection.

Quality scoring is experimental. The labelled examples in
`data/quality_evaluation.jsonl` can be evaluated with:

```bash
python -m utils.evaluate_quality
```

The score is a content-quality signal, not a factuality or source-trust claim.

Article analyses also retain explicit attribution sentences and linked URLs as
evidence records. Evidence extraction identifies possible support; it does not
verify that a claim is true.

The dashboard includes an installable PWA shell through a manifest and service
worker. CI runs compilation, tests, and diff hygiene through GitHub Actions.
Source contributors can implement the `SourceAdapter` protocol in
`sources/base.py` and register adapters through `sources/registry.py`.

The first administrator can be created once with
`POST /api/v1/auth/bootstrap` using `TECHSCOPE_BOOTSTRAP_SECRET`. Subsequent
requests can use the returned bearer token with `Authorization: Bearer ...`.

## Feed Operations

Register a public feed, then run ingestion:

```bash
curl -X POST http://localhost:8000/api/v1/feeds \
	-H "x-api-key: $TECHSCOPE_API_KEY" \
	-H "content-type: application/json" \
	-d '{"url":"https://www.theverge.com/rss/index.xml","name":"The Verge"}'

curl -X POST http://localhost:8000/api/v1/ingest \
	-H "x-api-key: $TECHSCOPE_API_KEY"
```

Ingestion returns `202 Accepted` with a job record. Poll the returned job ID:

```bash
curl http://localhost:8000/api/v1/jobs/{job_id} \
	-H "x-api-key: $TECHSCOPE_API_KEY"
```

The scheduler uses enabled registered feeds and falls back to the built-in tech
feed list only when no feeds have been configured. Feed state records preserve
ETag, Last-Modified, and fetch error information.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

The Compose stack runs the API, authenticated dashboard, PostgreSQL, and
Redis-backed rate limiting. Local development defaults to SQLite when
`DATABASE_URL` is not set. Schema version `1` is applied automatically at
startup; the application preserves the same repository API across both
backends.

## Development Status

The project is being developed as a feed-driven technology intelligence
platform. Remaining major work includes larger independent evaluation data,
reliable webhook retry/dead-letter handling, full observability, a complete
mobile reading experience, and a packaged source-adapter SDK.

## Tests

```bash
python -m unittest discover -s tests -v
```