import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("articles.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS articles
                 (summary TEXT, credibility REAL, keywords TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

def write_to_db(summary, credibility, keywords):
    timestamp = datetime.utcnow().isoformat()
    conn = sqlite3.connect("articles.db")
    c = conn.cursor()
    c.execute("INSERT INTO articles VALUES (?, ?, ?, ?)",
              (summary, credibility, ",".join(keywords), timestamp))
    conn.commit()
    conn.close()
