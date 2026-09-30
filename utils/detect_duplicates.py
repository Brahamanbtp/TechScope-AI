from typing import List, Tuple
import hashlib

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    SentenceTransformer = None
    util = None

# Load model once (MiniLM is fast & accurate for semantic similarity)
model = None

def compute_embeddings(texts: List[str]):
    """Generate embeddings for a list of texts."""
    global model
    if SentenceTransformer is None:
        raise RuntimeError("sentence-transformers is not installed")
    if model is None:
        model = SentenceTransformer('all-MiniLM-L6-v2')
    return model.encode(texts, convert_to_tensor=True, normalize_embeddings=True)

def detect_similar_articles(articles: List[str], threshold: float = 0.9) -> List[Tuple[int, int, float]]:
    """
    Detect similar articles by computing pairwise cosine similarity.

    Args:
        articles: List of article texts (already cleaned).
        threshold: Cosine similarity threshold to flag as duplicates.

    Returns:
        List of tuples: (index1, index2, similarity_score)
    """
    if not articles:
        return []

    if SentenceTransformer is None:
        seen = {}
        duplicates = []
        for index, article in enumerate(articles):
            fingerprint = hashlib.sha256(article.strip().lower().encode()).hexdigest()
            if fingerprint in seen:
                duplicates.append((seen[fingerprint], index, 1.0))
            else:
                seen[fingerprint] = index
        return duplicates

    duplicates = []
    embeddings = compute_embeddings(articles)

    # Compute upper triangle of similarity matrix
    for i in range(len(articles)):
        for j in range(i + 1, len(articles)):
            sim = float(util.cos_sim(embeddings[i], embeddings[j]))
            if sim >= threshold:
                duplicates.append((i, j, round(sim, 4)))

    return duplicates
