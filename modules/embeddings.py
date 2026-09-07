from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# LOAD EMBEDDING MODEL
# ============================================================

_model = None


def get_embedding_model():

    global _model

    if _model is None:

        _model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

    return _model


# ============================================================
# CREATE CHUNK EMBEDDINGS
# ============================================================

def create_embeddings(chunks):

    if not chunks:
        return chunks

    model = get_embedding_model()

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=False
    )

    for chunk, embedding in zip(
        chunks,
        embeddings
    ):

        chunk["embedding"] = embedding

    return chunks


# ============================================================
# SEMANTIC SEARCH
# ============================================================

def semantic_search(
    question,
    chunks,
    top_k=5
):

    if not chunks:
        return []


    model = get_embedding_model()


    # Question embedding
    question_embedding = model.encode(
        [question],
        convert_to_numpy=True
    )


    # Only chunks that have embeddings
    valid_chunks = [
        chunk
        for chunk in chunks
        if "embedding" in chunk
    ]


    if not valid_chunks:
        return []


    chunk_embeddings = [
        chunk["embedding"]
        for chunk in valid_chunks
    ]


    similarities = cosine_similarity(
        question_embedding,
        chunk_embeddings
    )[0]


    results = []


    for chunk, similarity in zip(
        valid_chunks,
        similarities
    ):

        results.append({
            "page": chunk["page"],
            "text": chunk["text"],
            "score": float(similarity)
        })


    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )


    return results[:top_k]