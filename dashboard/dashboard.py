from fastapi import FastAPI, Request, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import json

from utils.save_data import load_articles
from api.auth import verify_api_key

# --- Initialization ---
app = FastAPI(title="TechScope Dashboard", version="1.0")

# --- Path Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# --- Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# --- Template Engine ---
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# --- Static Files (for CSS/JS) ---
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- CORS for Frontend Integration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("TECHSCOPE_CORS_ORIGINS", "http://localhost:8501").split(","),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Route: HTML Dashboard ---
@app.get("/", response_class=HTMLResponse, dependencies=[Depends(verify_api_key)])
def read_dashboard(
    request: Request,
    search: str | None = Query(default=None, max_length=200),
    source: str | None = Query(default=None, max_length=200),
    min_quality: float | None = Query(default=None, ge=0, le=1),
):
    try:
        articles = _dashboard_articles(search, source, min_quality)

        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={"articles": articles},
        )

    except Exception as e:
        logging.error(f"Error loading dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to load dashboard.")

# --- Optional JSON API Endpoint ---
@app.get("/api/records", response_class=JSONResponse, dependencies=[Depends(verify_api_key)])
def get_records(
    search: str | None = Query(default=None, max_length=200),
    source: str | None = Query(default=None, max_length=200),
    min_quality: float | None = Query(default=None, ge=0, le=1),
):
    try:
        articles = _dashboard_articles(search, source, min_quality)

        return {"count": len(articles), "articles": articles}

    except Exception as e:
        logging.error(f"API error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve records.")


def _dashboard_articles(search, source, min_quality):
    articles = load_articles(
        limit=100,
        search=search,
        source=source,
        min_quality=min_quality,
    )
    for article in articles:
        article["keywords"] = [word for word in article.get("keywords", "").split(",") if word]
        try:
            article["quality_signals"] = json.loads(article.get("quality_explanation", "") or "[]")
        except (TypeError, json.JSONDecodeError):
            article["quality_signals"] = []
        article["credibility"] = article.get("quality_score") or article.get("credibility")
    return articles
