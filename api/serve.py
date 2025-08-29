import sys
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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
from utils.credibility import score_credibility
from utils.keywords import extract_keywords
from utils.save_data import load_articles
from utils.auth import verify_api_key

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
    allow_origins=["*"],  # Change to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------
# Pydantic input model
# --------------------------
class ArticleInput(BaseModel):
    text: str

# --------------------------
# Routes
# --------------------------

@app.get("/")
def root():
    return {"message": "🚀 Welcome to TechScope AI - FastAPI Backend"}

@app.get("/articles")
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
        score = score_credibility(input.text)
        return {"credibility_score": score}
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

# --------------------------
# Run server (dev mode)
# --------------------------
if __name__ == "__main__":
    uvicorn.run("api.serve:app", host="0.0.0.0", port=8000, reload=True)
