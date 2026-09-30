import sys
import os
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

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
from utils.save_data import load_articles
from storage.schema import write_article
from utils.rate_limit import enforce_analyze_rate_limit
from utils.url_fetcher import FetchError, fetch_article
from api.auth import verify_api_key

# --------------------------
# FastAPI app
# --------------------------
app = FastAPI(
    title="🧠 TechScope AI",
    description="Summarized Tech News API with Credibility & Keywords",
    version="1.0.0"
)

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

# --------------------------
# Routes
# --------------------------

@app.get("/")
def root():
    return {"message": "🚀 Welcome to TechScope AI - FastAPI Backend"}

@app.get("/articles", dependencies=[Depends(verify_api_key)])
def get_articles():
    """Load stored articles"""
    try:
        articles = load_articles()
        return {"articles": articles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/summarize", dependencies=[Depends(verify_api_key)])
def summarize_text(input: ArticleInput):
    """Summarize text (API key protected)"""
    try:
        summary = summarize_article(input.text)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/keywords", dependencies=[Depends(verify_api_key)])
def get_keywords(input: ArticleInput):
    """Extract keywords (API key protected)"""
    try:
        keywords = extract_keywords(input.text)
        return {"keywords": keywords}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        write_article(article)
        return {
            "url": article["url"],
            "title": article["title"],
            "source": article["source"],
            "summary": article["summary"],
            "keywords": article["keywords"],
            "credibility": article["credibility"],
            "quality": quality,
        }
    except FetchError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Article analysis failed") from exc

# --------------------------
# Run server (dev mode)
# --------------------------
if __name__ == "__main__":
    uvicorn.run("api.serve:app", host="0.0.0.0", port=8000, reload=True)
