# 🧠 TechScope AI

TechScope AI is an advanced **AI-powered tech news dashboard** that summarizes technology articles, scores their credibility, and extracts keywords. Built with **FastAPI**, **SQLite**, **Streamlit**, and **HuggingFace Transformers**, it provides a full-stack solution for tech news analysis.

---
## Features

- ✅ Summarize tech articles using HuggingFace Transformers
- ✅ Credibility scoring for news articles
- ✅ Keyword extraction from article text
- ✅ FastAPI backend with API key authentication
- ✅ Streamlit frontend dashboard
- ✅ Persistent storage with SQLite (`techscope.db`)
- ✅ Fully RESTful API endpoints
- ✅ CORS-enabled for frontend integration
- ✅ Docker / Codespaces compatible

---

## Tech Stack

- **Backend:** Python, FastAPI
- **Frontend:** Streamlit
- **Database:** SQLite
- **NLP:** HuggingFace Transformers, Sentence-BERT
- **Other:** Pydantic, Uvicorn, CORSMiddleware

---

## Project Structure
```
TechScope-AI/
├── api/
│ ├── serve.py         # FastAPI backend
│ └── auth.py          # API key authentication
├── utils/
│ ├── summarizer.py    # Summarization utilities
│ ├── credibility.py   # Credibility scoring
│ ├── keywords.py      # Keyword extraction
│ └── save_data.py     # Load/save articles from DB
├── dashboard/
│ └── dashboard.py     # Streamlit frontend
├── data/
│ └── techscope.db     # SQLite database
├── templates/         # Optional HTML templates
├── static/            # Optional CSS/JS files
├── requirements.txt   # Python dependencies
└── README.md
```
---

## Setup Instructions

### 1. Clone Repository
```bash
git clone https://github.com/Brahamanbtp/TechScope-AI.git
cd TechScope-AI
```
### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
```
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
### Dependencies include:
---
- `fastapi==0.113.0`
- `uvicorn[standard]==0.23.2`
- `streamlit==1.28.0`
- `pydantic==2.7.1`
- `requests==2.32.0`
- `sentence-transformers==2.2.2`
- `transformers==5.7.0`
- `torch==2.2.0`
- `typing-extensions==5.3.0`
- `jinja2==3.1.3`

---

### 4. Initialize SQLite Database
```bash
sqlite3 data/techscope.db
```
```bash
# Create summaries table if not exists:
CREATE TABLE IF NOT EXISTS summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary TEXT,
    credibility REAL,
    keywords TEXT,
    created_at TEXT
);
Insert sample data (optional):
```
```bash
INSERT INTO summaries (summary, credibility, keywords, created_at)
VALUES
('OpenAI releases GPT-5 with enhanced reasoning capabilities and real-time memory.', 0.96, 'OpenAI,GPT-5,AI', '2025-07-22 10:00:00'),
('Google launches Gemini 2 to compete with ChatGPT in global markets.', 0.92, 'Google,Gemini,AI', '2025-07-21 14:30:00');
```

## Running the Application
### 1. Start FastAPI Backend
```bash
python -m uvicorn api.serve:app --reload --host 0.0.0.0 --port 8000
```
---
#### Backend endpoints:

|Method	|Endpoint	    |Description|
|-------|-----------    |------------|
|GET	|/	            |Root, returns welcome message|
|GET	|/articles	    |Load all stored articles|
|POST	|/summarize	    |Summarize text (API key required)|
|POST	|/credibility	|Get credibility score (API key required)|
|POST	|/keywords	    |Extract keywords (API key required)|
---

### 2. Start Streamlit Dashboard
```bash
python -m streamlit run dashboard/dashboard.py  
```

#### Dashboard Features:

- Shows AI-summarized articles

- Displays credibility score and keywords

- Supports caching for faster updates

- User-friendly UI with Streamlit containers and expanders

### API Key Authentication
- API key required for `/summarize`, `/credibility`, `/keywords`

- Verify with x-api-key header

- Implement your own API key in `api/auth.py`

### Notes
- Backend uses CPU by default; can be changed to GPU if available

- FastAPI supports CORS, so frontend can be hosted separately

- Streamlit caching ensures minimal API calls

- SQLite database is lightweight and persistent for development
--- 
### Troubleshooting
#### 1. `command not found` errors for uvicorn/streamlit

```bash
python -m uvicorn api.serve:app --reload
python -m streamlit run dashboard/dashboard.py
```
#### 2. No articles showing in dashboard

- Ensure `techscope.db` contains data in `summaries` table

- Ensure backend is running and API URL is correct in `dashboard.py` (`API_URL`)

#### 3. Reinstall dependencies

```bash
pip install --upgrade -r requirements.txt
```
---
### Future Enhancements
- Real-time news scraping and auto-summarization

- User authentication for personalized dashboards

- Multi-language support for articles

- Export articles and summaries to PDF/CSV

- Docker deployment for easy hosting

## License
- MIT License

## Author
#### Pranay Sharma
