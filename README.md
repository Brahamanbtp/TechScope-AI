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
| GET | `/articles` | Stored articles |
| POST | `/summarize` | Summarize text; requires `x-api-key` |
| POST | `/credibility` | Return explainable quality signals; requires `x-api-key` |
| POST | `/keywords` | Extract keywords; requires `x-api-key` |
| POST | `/analyze` | Fetch and analyze a public article URL; requires `x-api-key` |

Analysis requests must contain between 100 and 100,000 characters in `text`.
URL analysis accepts only public HTTP(S) URLs, does not follow redirects, limits
responses to 2 MB, and is rate-limited per client address.

## Run the Dashboard

```bash
python -m uvicorn dashboard.dashboard:app --reload --port 8501
```

The dashboard reads the same `articles` table as the API.

## Configuration

See `.env.example` for supported settings:

- `TECHSCOPE_API_KEY`
- `TECHSCOPE_CORS_ORIGINS`
- `USE_OPENAI`
- `OPENAI_API_KEY`

AI models are loaded lazily. Without optional model packages or a model cache,
the application uses extractive summarization, frequency-based keywords, and
exact-text duplicate detection.

## Development Status

The project is being consolidated from an earlier prototype. Source adapters,
advanced model evaluation, distributed rate limiting, and production scheduling
remain follow-up work.

## Tests

```bash
python -m unittest discover -s tests -v
```