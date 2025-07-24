from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import logging

from utils.scraper import scrape_website
from utils.summarizer import summarize_text
from utils.keywords import extract_keywords
from utils.credibility import calculate_credibility

from storage.json_writer import write_to_json
from storage.csv_writer import write_to_csv
from storage.db_writer import write_to_db, init_db
from storage.mongo_writer import write_to_mongo

# --- Initialization ---
app = FastAPI(title="TechScope API", version="1.0")
init_db()

# --- Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request Schema ---
class URLInput(BaseModel):
    url: str
    mode: Optional[str] = "json"  # json, csv, db, mongo

# --- Routes ---

@app.get("/")
def read_root():
    return {"TechScope": "Summarization and Credibility API", "status": "Running"}

@app.post("/analyze/")
def analyze_url(input: URLInput):
    try:
        logging.info(f"Received request for URL: {input.url}")

        # Step 1: Scrape content
        content = scrape_website(input.url)
        if not content:
            raise HTTPException(status_code=404, detail="Content could not be scraped.")

        # Step 2: Summarize
        summary = summarize_text(content)

        # Step 3: Keywords
        keywords = extract_keywords(content)

        # Step 4: Credibility
        score = calculate_credibility(content)

        # Step 5: Result
        result = {
            "url": input.url,
            "summary": summary,
            "keywords": keywords,
            "credibility": round(score, 2)
        }

        # Step 6: Store based on mode
        if input.mode == "json":
            write_to_json(result)
        elif input.mode == "csv":
            write_to_csv(result)
        elif input.mode == "db":
            write_to_db(summary, score, keywords)
        elif input.mode == "mongo":
            write_to_mongo(result)
        else:
            logging.warning(f"Unknown storage mode: {input.mode}")

        logging.info(f"Processed URL successfully: {input.url}")
        return result

    except Exception as e:
        logging.error(f"Error processing URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))
