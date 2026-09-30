import sys
import os
from fastapi import FastAPI, HTTPException, Depends, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
import logging

# --------------------------
# Ensure project root is in sys.path
# --------------------------
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# --------------------------
# Import utils
# --------------------------
from utils.summarizer import summarize_article
from utils.credibility import assess_content_quality
from utils.keywords import extract_keywords
from utils.save_data import count_articles, load_articles
from storage.schema import write_article
from storage.article_repo import get_article
from storage.feed_repo import create_feed, delete_feed, get_feed, list_feed_health, list_feeds
from storage.job_repo import get_job
from utils.rate_limit import enforce_analyze_rate_limit
from utils.url_fetcher import FetchError, fetch_article
from api.auth import verify_admin, verify_api_key
from utils.scheduler import ingest_feeds_once
from utils.url_fetcher import validate_public_url
from utils.job_runner import submit_ingest_job
from storage.user_repo import authenticate_user, count_users, create_session, create_user
from storage.cluster_repo import list_clusters
from utils.clustering import cluster_articles
from utils.evidence import extract_evidence

# --------------------------
# FastAPI app
# --------------------------
app = FastAPI(
    title="🧠 TechScope AI",
    description="Summarized Tech News API with Credibility & Keywords",
    version="1.0.0"
)

logger = logging.getLogger("techscope.api")

allowed_hosts = os.getenv("TECHSCOPE_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response

# CORS configuration for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("TECHSCOPE_CORS_ORIGINS", "http://localhost:8501").split(","),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------
# Pydantic input model
# --------------------------
class ArticleInput(BaseModel):
    text: str = Field(..., min_length=100, max_length=100_000)


class UrlInput(BaseModel):
    url: str = Field(..., min_length=8, max_length=2_000)


class FeedInput(BaseModel):
    url: str = Field(..., min_length=8, max_length=2_000)
    name: str = Field(default="", max_length=200)
    interval_minutes: int = Field(default=30, ge=5, le=1_440)


class LoginInput(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=12, max_length=200)


class BootstrapInput(LoginInput):
    bootstrap_secret: str = Field(..., min_length=16, max_length=200)

# --------------------------
# Routes
# --------------------------

@app.get("/")
def root():
    return {"message": "🚀 Welcome to TechScope AI - FastAPI Backend"}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/api/v1/auth/login")
def login(input: LoginInput):
    user = authenticate_user(input.username, input.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": create_session(user["id"]), "token_type": "bearer", "user": {"username": user["username"], "role": user["role"]}}


@app.post("/api/v1/auth/bootstrap", status_code=status.HTTP_201_CREATED)
def bootstrap(input: BootstrapInput):
    expected = os.getenv("TECHSCOPE_BOOTSTRAP_SECRET")
    if not expected or input.bootstrap_secret != expected:
        raise HTTPException(status_code=403, detail="Invalid bootstrap secret")
    if count_users() > 0:
        raise HTTPException(status_code=409, detail="Bootstrap is already complete")
    try:
        return create_user(input.username, input.password, role="admin")
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc):
            raise HTTPException(status_code=409, detail="User already exists") from exc
        raise HTTPException(status_code=500, detail="User could not be created") from exc

@app.get("/articles", dependencies=[Depends(verify_api_key)])
def get_articles(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, max_length=200),
    source: str | None = Query(default=None, max_length=200),
    min_quality: float | None = Query(default=None, ge=0, le=1),
):
    """Load stored articles"""
    try:
        articles = load_articles(
            limit=limit,
            offset=offset,
            search=search,
            source=source,
            min_quality=min_quality,
        )
        return {
            "articles": articles,
            "count": count_articles(search, source, min_quality),
            "limit": limit,
            "offset": offset,
        }
    except Exception:
        logger.exception("Failed to load articles")
        raise HTTPException(status_code=500, detail="Articles could not be loaded")

@app.post("/summarize", dependencies=[Depends(verify_api_key)])
def summarize_text(input: ArticleInput):
    """Summarize text (API key protected)"""
    try:
        summary = summarize_article(input.text)
        return {"summary": summary}
    except Exception:
        logger.exception("Summarization failed")
        raise HTTPException(status_code=500, detail="Summarization failed")

@app.post("/credibility", dependencies=[Depends(verify_api_key)])
def get_credibility(input: ArticleInput):
    """Get credibility score (API key protected)"""
    try:
        assessment = assess_content_quality(input.text)
        return {
            "credibility_score": assessment["score"],
            "quality_score": assessment["score"],
            "quality_label": assessment["label"],
            "quality_signals": assessment["signals"],
            "analysis_version": assessment["method"],
            "quality_reliability": assessment["reliability"],
        }
    except Exception:
        logger.exception("Quality assessment failed")
        raise HTTPException(status_code=500, detail="Quality assessment failed")

@app.post("/keywords", dependencies=[Depends(verify_api_key)])
def get_keywords(input: ArticleInput):
    """Extract keywords (API key protected)"""
    try:
        keywords = extract_keywords(input.text)
        return {"keywords": keywords}
    except Exception:
        logger.exception("Keyword extraction failed")
        raise HTTPException(status_code=500, detail="Keyword extraction failed")


@app.post("/analyze", dependencies=[Depends(verify_api_key), Depends(enforce_analyze_rate_limit)])
def analyze_url(input: UrlInput):
    try:
        article = fetch_article(input.url)
        content = article["content"]
        quality = assess_content_quality(content)
        article["summary"] = summarize_article(content)
        article["keywords"] = extract_keywords(content)
        article["credibility"] = quality["score"]
        article["quality_score"] = quality["score"]
        article["quality_explanation"] = quality["signals"]
        article["analysis_version"] = quality["method"]
        article["evidence"] = extract_evidence(content)
        write_article(article)
        return {
            "url": article["url"],
            "title": article["title"],
            "source": article["source"],
            "summary": article["summary"],
            "keywords": article["keywords"],
            "credibility": article["credibility"],
            "quality": quality,
            "evidence": article["evidence"],
        }
    except FetchError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Article analysis failed") from exc


@app.get("/api/v1/feeds", dependencies=[Depends(verify_api_key)])
def get_feeds():
    return {"feeds": list_feeds()}


@app.get("/api/v1/feeds/health", dependencies=[Depends(verify_api_key)])
def get_feed_health():
    return {"feeds": list_feed_health()}


@app.post("/api/v1/feeds", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_admin)])
def add_feed(input: FeedInput):
    try:
        url = validate_public_url(input.url)
        return create_feed(url, input.name, input.interval_minutes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc):
            raise HTTPException(status_code=409, detail="Feed already exists") from exc
        logger.exception("Failed to create feed")
        raise HTTPException(status_code=500, detail="Feed could not be created") from exc


@app.delete("/api/v1/feeds/{feed_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_admin)])
def remove_feed(feed_id: int):
    if not delete_feed(feed_id):
        raise HTTPException(status_code=404, detail="Feed not found")


@app.post("/api/v1/ingest", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(verify_admin), Depends(enforce_analyze_rate_limit)])
def ingest_now():
    return submit_ingest_job()


@app.get("/api/v1/jobs/{job_id}", dependencies=[Depends(verify_api_key)])
def get_job_status(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/v1/articles/{article_id}", dependencies=[Depends(verify_api_key)])
def get_article_detail(article_id: int):
    article = get_article(article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    try:
        article["evidence"] = json.loads(article.get("evidence_json", "[]") or "[]")
    except json.JSONDecodeError:
        article["evidence"] = []
    return article


@app.post("/api/v1/clusters/rebuild", dependencies=[Depends(verify_admin)])
def rebuild_clusters():
    return cluster_articles()


@app.get("/api/v1/clusters", dependencies=[Depends(verify_api_key)])
def get_clusters():
    return {"clusters": list_clusters()}

# --------------------------
# Run server (dev mode)
# --------------------------
if __name__ == "__main__":
    uvicorn.run("api.serve:app", host="0.0.0.0", port=8000, reload=True)
