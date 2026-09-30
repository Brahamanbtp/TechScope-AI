from storage.cluster_repo import load_cluster_documents


def semantic_search(query: str, limit: int = 20) -> list[dict]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    documents = load_cluster_documents()
    if not documents or not query.strip():
        return []
    texts = [f"{item['title']} {item['summary']} {item['content']}" for item in documents]
    vectorizer = TfidfVectorizer(stop_words="english", max_features=20_000)
    matrix = vectorizer.fit_transform(texts)
    query_vector = vectorizer.transform([query])
    scores = cosine_similarity(query_vector, matrix)[0]
    ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
    return [
        {"id": documents[index]["id"], "title": documents[index]["title"], "score": round(float(score), 4)}
        for index, score in ranked[:limit]
        if score > 0
    ]