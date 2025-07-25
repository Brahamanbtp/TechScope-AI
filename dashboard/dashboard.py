from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import logging
import os

# --- Initialization ---
app = FastAPI(title="TechScope Dashboard", version="1.0")

# --- Path Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "techscope.db"))

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
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Route: HTML Dashboard ---
@app.get("/", response_class=HTMLResponse)
def read_dashboard(request: Request):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT id, summary, credibility, keywords, created_at FROM summaries ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

        articles = [
            {
                "id": row[0],
                "summary": row[1],
                "credibility": row[2],
                "keywords": row[3].split(','),
                "created_at": row[4]
            }
            for row in rows
        ]

        return templates.TemplateResponse("dashboard.html", {"request": request, "articles": articles})

    except Exception as e:
        logging.error(f"Error loading dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to load dashboard.")

# --- Optional JSON API Endpoint ---
@app.get("/api/records", response_class=JSONResponse)
def get_records():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT id, summary, credibility, keywords, created_at FROM summaries ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

        articles = [
            {
                "id": row[0],
                "summary": row[1],
                "credibility": row[2],
                "keywords": row[3].split(','),
                "created_at": row[4]
            }
            for row in rows
        ]

        return {"count": len(articles), "articles": articles}

    except Exception as e:
        logging.error(f"API error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve records.")
