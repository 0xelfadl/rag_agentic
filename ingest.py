from pathlib import Path

from chunker import chunk_document, parse_front_matter
from db import connect
from embeddings import embed_documents


def embedding_text(title: str, chunk: dict) -> str:
    """What the embedding model reads: breadcrumb + content. Never stored."""
    breadcrumb = " > ".join(part for part in [title, chunk["heading_path"]] if part)
    return f"{breadcrumb}\n\n{chunk['content']}"


def main():
    files = sorted(Path("data").glob("*.md"))

    with connect() as conn:
        # Start from a clean state. ON DELETE CASCADE removes the chunks too.
        conn.execute("DELETE FROM documents")

        for file in files:
            meta, body = parse_front_matter(file.read_text(encoding="utf-8"))
            chunks = chunk_document(body)
            vectors = embed_documents(
                [embedding_text(meta["title"], chunk) for chunk in chunks]
            )

            document_id = conn.execute(
                "INSERT INTO documents (slug, title, doc_type) VALUES (%s, %s, %s) RETURNING id",
                (file.stem, meta["title"], meta["type"]),
            ).fetchone()[0]

            for chunk, vector in zip(chunks, vectors):
                conn.execute(
                    """
                    INSERT INTO chunks (document_id, chunk_index, heading_path, content, embedding)
                    VALUES (%s, %s, %s, %s, %s::vector)
                    """,
                    (
                        document_id,
                        chunk["chunk_index"],
                        chunk["heading_path"],
                        chunk["content"],
                        vector,
                    ),
                )
            print(f"+ {file.stem}: {len(chunks)} chunks")

        total = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]

    print(f"Done: {total} chunks stored")


if __name__ == "__main__":
    main()
