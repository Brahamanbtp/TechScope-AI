from storage.cluster_repo import save_cluster_assignments


def cluster_articles(threshold: float = 0.35) -> dict:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    from storage.cluster_repo import load_cluster_documents

    documents = load_cluster_documents()
    if not documents:
        return {"articles": 0, "clusters": 0, "method": "tfidf-v1"}

    texts = [f"{item['title']} {item['summary']} {item['content']}" for item in documents]
    matrix = TfidfVectorizer(stop_words="english", max_features=20_000).fit_transform(texts)
    similarities = cosine_similarity(matrix)
    parents = list(range(len(documents)))

    def find(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left, right):
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parents[root_right] = root_left

    for left in range(len(documents)):
        for right in range(left + 1, len(documents)):
            if similarities[left, right] >= threshold:
                union(left, right)

    roots = {}
    assignments = {}
    for index, document in enumerate(documents):
        root = find(index)
        cluster_id = roots.setdefault(root, f"cluster-{len(roots) + 1}")
        assignments[document["id"]] = cluster_id
    save_cluster_assignments(assignments)
    return {"articles": len(documents), "clusters": len(set(assignments.values())), "method": "tfidf-v1"}