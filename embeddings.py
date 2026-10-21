import ollama

from db import EMBEDDING_DIM

MODEL = "qwen3-embedding:0.6b"

# qwen3-embedding was trained to expect an instruction before QUESTIONS (not before documents).
QUERY_INSTRUCTION = (
    "Instruct: Given a user question, retrieve passages from product documentation that answer it\n"
    "Query: "
)


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed many chunks in one call (a batch)."""
    vectors = ollama.embed(model=MODEL, input=texts).embeddings
    for vector in vectors:
        check_size(vector)
    return vectors


def embed_query(question: str) -> list[float]:
    """Embed one user question, with the instruction in front."""
    vector = ollama.embed(model=MODEL, input=QUERY_INSTRUCTION + question).embeddings[0]
    # for vector in vectors:
    check_size(vector)
    return vector


def check_size(vector: list[float]) -> None:
    if len(vector) != EMBEDDING_DIM:
        raise ValueError(
            f"{MODEL} returned {len(vector)} numbers,but the database expects {EMBEDDING_DIM} "
        )
