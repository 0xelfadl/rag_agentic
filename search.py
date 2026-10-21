import argparse

from db import connect
from embeddings import embed_query

# <=> is pgvector's cosine DISTANCE: 0 = same direction, 2 = opposite.
# We ORDER BY the distance (the index can use that) and show 1 - distance as a similarity score.
SEARCH_SQL = """
SELECT d.slug, c.chunk_index, d.title, c.heading_path, c.content,
       1 - (c.embedding <=> %(vector)s::vector) AS score
FROM chunks c
JOIN documents d ON d.id = c.document_id
WHERE (%(doc_type)s::text IS NULL OR d.doc_type = %(doc_type)s)
ORDER BY c.embedding <=> %(vector)s::vector
LIMIT %(top_k)s
"""


def search(question: str, top_k: int = 5, doc_type: str | None = None) -> list[dict]:
    """Return the top_k chunks closest in meaning to the question."""
    vector = embed_query(question)
    with connect() as conn:
        rows = conn.execute(
            SEARCH_SQL, {"vector": vector, "doc_type": doc_type, "top_k": top_k}
        ).fetchall()

    return [
        {
            "ref": f"{slug}#{chunk_index}",  # e.g. "faq#1": a short id the LLM can cite later
            "document": title,
            "section": heading_path,
            "score": round(score, 3),
            "text": content,
        }
        for slug, chunk_index, title, heading_path, content, score in rows
    ]


def main():
    parser = argparse.ArgumentParser(
        description="Semantic search over the Voltway documents"
    )
    parser.add_argument("question")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--type", choices=["faq", "policy", "manual", "release-notes"])
    args = parser.parse_args()

    print(f"Question: {args.question}\n")
    for hit in search(args.question, args.top_k, args.type):
        print(f"{hit['score']:.3f}  {hit['ref']:<30} {hit['section'] or '(intro)'}")


if __name__ == "__main__":
    main()
