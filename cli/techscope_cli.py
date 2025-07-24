import typer
import requests
from bs4 import BeautifulSoup
import sqlite3
import json
import os
from datetime import datetime
from uuid import uuid4
import re

app = typer.Typer()

# === Constants ===
STORAGE_DIR = "storage"
DB_PATH = os.path.join(STORAGE_DIR, "techscope.db")
JSON_PATH = os.path.join(STORAGE_DIR, "techscope.json")
TEXT_PATH = os.path.join(STORAGE_DIR, "techscope.txt")

# === Ensure storage directory exists ===
os.makedirs(STORAGE_DIR, exist_ok=True)

# === DB Setup ===
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS summaries (
        id TEXT PRIMARY KEY,
        summary TEXT,
        credibility REAL,
        keywords TEXT,
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()

# === Core Functions ===
def fetch_article_content(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        content = ' '.join(p.get_text() for p in paragraphs)
        return re.sub(r'\s+', ' ', content.strip())
    except Exception as e:
        typer.secho(f"[ERROR] Failed to fetch content: {e}", fg=typer.colors.RED)
        raise typer.Exit()

def summarize_text(text: str, max_sentences=5) -> str:
    sentences = re.split(r'(?<=[.!?]) +', text)
    summary = ' '.join(sentences[:max_sentences])
    return summary.strip()

def calculate_credibility(text: str) -> float:
    credibility = 100.0
    bad_indicators = ['rumor', 'unverified', 'alleged', 'reportedly', 'according to sources']
    penalty = sum(text.lower().count(word) for word in bad_indicators)
    credibility -= penalty * 10
    return max(credibility, 0.0)

def extract_keywords(text: str, top_n=5) -> list:
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    common = {}
    for word in words:
        common[word] = common.get(word, 0) + 1
    sorted_keywords = sorted(common.items(), key=lambda x: x[1], reverse=True)
    return [kw[0] for kw in sorted_keywords[:top_n]]

def store_to_db(summary_data: dict):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO summaries (id, summary, credibility, keywords, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        summary_data["id"],
        summary_data["summary"],
        summary_data["credibility"],
        ','.join(summary_data["keywords"]),
        summary_data["created_at"]
    ))
    conn.commit()
    conn.close()

def store_to_json(summary_data: dict):
    data = []
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    data.append(summary_data)
    with open(JSON_PATH, 'w') as f:
        json.dump(data, f, indent=4)

def store_to_txt(summary_data: dict):
    with open(TEXT_PATH, 'a') as f:
        f.write(f"=== Summary ID: {summary_data['id']} ===\n")
        f.write(f"Created At: {summary_data['created_at']}\n")
        f.write(f"Summary: {summary_data['summary']}\n")
        f.write(f"Credibility Score: {summary_data['credibility']:.2f}\n")
        f.write(f"Keywords: {', '.join(summary_data['keywords'])}\n\n")

def save_summary(mode: str, summary_data: dict):
    if mode == "db":
        store_to_db(summary_data)
    elif mode == "json":
        store_to_json(summary_data)
    elif mode == "txt":
        store_to_txt(summary_data)
    else:
        typer.secho("Invalid storage mode.", fg=typer.colors.RED)
        raise typer.Exit()

# === CLI Command ===
@app.command()
def summarize(
    url: str = typer.Argument(..., help="News article URL to summarize"),
    storage: str = typer.Option("db", help="Storage mode: db / json / txt")
):
    """
    TechScope - Summarize and analyze the credibility of news articles.
    """
    typer.secho("🔍 Fetching content...", fg=typer.colors.BLUE)
    article = fetch_article_content(url)

    typer.secho("✂️ Generating summary...", fg=typer.colors.CYAN)
    summary = summarize_text(article)

    typer.secho("🧠 Calculating credibility...", fg=typer.colors.GREEN)
    credibility = calculate_credibility(article)

    typer.secho("🗂 Extracting keywords...", fg=typer.colors.YELLOW)
    keywords = extract_keywords(article)

    summary_data = {
        "id": str(uuid4()),
        "summary": summary,
        "credibility": credibility,
        "keywords": keywords,
        "created_at": datetime.now().isoformat()
    }

    typer.secho(f"💾 Saving summary using [{storage}] mode...", fg=typer.colors.MAGENTA)
    save_summary(storage, summary_data)

    typer.secho("✅ Summary saved successfully!\n", fg=typer.colors.GREEN, bold=True)
    typer.echo(f"Summary:\n{summary}\n")
    typer.echo(f"Credibility Score: {credibility:.2f}")
    typer.echo(f"Keywords: {', '.join(keywords)}")

# === Entry Point ===
if __name__ == "__main__":
    app()
