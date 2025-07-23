from sentence_transformers import SentenceTransformer, util
from typing import List, Tuple
import numpy as np

# Load model once (MiniLM is fast & accurate for semantic similarity)
model = SentenceTransformer('all-MiniLM-L6-v2')

def compute_embeddings(texts: List[str]) -> np.ndarray:
    """Generate embeddings for a list of texts."""
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
    duplicates = []
    embeddings = compute_embeddings(articles)

    # Compute upper triangle of similarity matrix
    for i in range(len(articles)):
        for j in range(i + 1, len(articles)):
            sim = float(util.cos_sim(embeddings[i], embeddings[j]))
            if sim >= threshold:
                duplicates.append((i, j, round(sim, 4)))

    return duplicates
