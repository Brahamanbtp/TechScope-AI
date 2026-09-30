from storage.schema import write_article

def init_db():
    from storage.schema import init_db as initialize_database
    initialize_database()

def write_to_db(summary, credibility, keywords):
    write_article({
        "url": f"local:{hash((summary, credibility, tuple(keywords)))}",
        "summary": summary,
        "credibility": credibility,
        "keywords": keywords,
    })
