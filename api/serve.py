from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from utils.summarizer import summarize_article
from utils.credibility import score_credibility
from utils.keywords import extract_keywords
from utils.save_data import load_articles
import uvicorn

app = FastAPI(title="🧠 TechScope AI", description="Summarized Tech News API with Credibility & Keywords")

# CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ArticleInput(BaseModel):
    text: str

@app.get("/")
def root():
    return {"message": "🚀 Welcome to TechScope AI - FastAPI Backend"}

@app.get("/articles")
def get_articles():
    try:
        articles = load_articles()
        return {"articles": articles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/summarize")
def summarize_text(input: ArticleInput):
    try:
        summary = summarize_article(input.text)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/credibility")
def get_credibility(input: ArticleInput):
    try:
        score = score_credibility(input.text)
        return {"credibility_score": score}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/keywords")
def get_keywords(input: ArticleInput):
    try:
        keywords = extract_keywords(input.text)
        return {"keywords": keywords}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("serve:app", host="0.0.0.0", port=8000, reload=True)
