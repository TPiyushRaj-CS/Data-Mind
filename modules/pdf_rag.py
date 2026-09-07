import re


def tokenize(text):
    """
    Convert text into simple lowercase words.
    """

    return set(
        re.findall(
            r"\b[a-zA-Z0-9]+\b",
            text.lower()
        )
    )


def calculate_relevance(
    question,
    chunk_text
):
    """
    Simple keyword-overlap retrieval.

    This is intentionally lightweight for the
    first version of DataMind AI.
    """

    question_words = tokenize(question)

    chunk_words = tokenize(chunk_text)

    if not question_words or not chunk_words:
        return 0

    common_words = (
        question_words.intersection(
            chunk_words
        )
    )

    return len(common_words)


def retrieve_relevant_chunks(
    question,
    chunks,
    top_k=5
):
    """
    Retrieve the most relevant PDF chunks.
    """

    scored_chunks = []

    for chunk in chunks:

        score = calculate_relevance(
            question,
            chunk["text"]
        )

        scored_chunks.append({
            "page": chunk["page"],
            "text": chunk["text"],
            "score": score
        })


    scored_chunks.sort(
        key=lambda x: x["score"],
        reverse=True
    )


    relevant_chunks = [
        chunk
        for chunk in scored_chunks[:top_k]
        if chunk["score"] > 0
    ]

    return relevant_chunks