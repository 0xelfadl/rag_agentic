import re
from itertools import pairwise
from pathlib import Path

MAX_CHARS = (
    1000  # about 250 tokens: big enough for a full answer, small enough for one topic
)
OVERLAP_CHARS = (
    200  # how much of the end of a chunk we repeat at the start of the next one
)


def parse_front_matter(raw: str) -> tuple[dict, str]:
    """Separate the '---' header block (title, type) from the document body."""
    if not raw.startswith("---\n"):
        return {}, raw
    header, body = raw[4:].split("\n---\n", 1)
    meta = {}
    for line in header.splitlines():
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta, body


def split_into_sections(body: str) -> list[dict]:
    """Cut the document at every heading. Each section remembers its heading path."""
    sections = []
    headings = []
    lines = []

    def close_section():
        text = "\n".join(lines).strip()
        if text:
            sections.append(
                {
                    "heading_path": " > ".join(
                        headings[1:]
                    ),  # [1:] skips the H1, it's the document title
                    "text": text,
                }
            )
        lines.clear()

    for line in body.splitlines():
        if line.startswith("#"):
            close_section()
            level = len(line) - len(line.lstrip("#"))  # "## Charging" -> 2
            title = line.lstrip("#").strip()
            del headings[level - 1 :]  # going back up? forget the deeper headings
            headings.append(title)
        else:
            lines.append(line)
    close_section()
    return sections


def split_sentences(text: str) -> list[str]:
    """Cut after . ! or ? when a space or newline follows."""
    return re.split(r"(?<=[.!?])\s+", text)


def last_sentences(sentences: list[str]) -> list[str]:
    """The last sentences that fit in OVERLAP_CHARS: they start the next chunk."""
    tail = []
    for sentence in reversed(sentences):
        if len(" ".join([sentence] + tail)) > OVERLAP_CHARS:
            break
        tail.insert(0, sentence)
    return tail


def split_long_text(text: str) -> list[str]:
    """Short text stays whole. Long text is packed sentence by sentence into chunks."""
    if len(text) <= MAX_CHARS:
        return [text]

    chunks = []
    current = []  # the sentences of the chunk we are filling

    for sentence in split_sentences(text):
        if current and len(" ".join(current + [sentence])) > MAX_CHARS:
            chunks.append(" ".join(current))  # this chunk is full: save it
            current = last_sentences(current)  # start the next one with the overlap
            if len(" ".join(current + [sentence])) > MAX_CHARS:
                current = []  # overlap + sentence would be too big: skip the overlap
        current.append(sentence)

    chunks.append(" ".join(current))
    return chunks


def chunk_document(body: str) -> list[dict]:
    """Sections first (3a), then split the long ones (3b)."""
    chunks = []
    for section in split_into_sections(body):
        for piece in split_long_text(section["text"]):
            chunks.append(
                {
                    "chunk_index": len(chunks),
                    "heading_path": section["heading_path"],
                    "content": piece,
                }
            )
    return chunks


def main():
    total = 0
    for file in sorted(Path("data").glob("*.md")):
        meta, body = parse_front_matter(file.read_text(encoding="utf-8"))
        chunks = chunk_document(body)
        total += len(chunks)
        print(f"\n{meta['title']}: {len(chunks)} chunks")
        for chunk in chunks:
            print(
                f"  #{chunk['chunk_index']:<2} {len(chunk['content']):>5} chars | {chunk['heading_path'] or '(intro)'}"
            )

        # Show where the split sections were cut, to check the overlap with our own eyes.
        for before, after in pairwise(chunks):
            if before["heading_path"] == after["heading_path"]:
                print(
                    f"\n  --- end of #{before['chunk_index']}: ...{before['content'][-90:]}"
                )
                print(
                    f"  --- start of #{after['chunk_index']}: {after['content'][:90]}..."
                )
    print(f"\nTotal: {total} chunks")


if __name__ == "__main__":
    main()
