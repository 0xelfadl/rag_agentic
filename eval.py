import json
import sys
from pathlib import Path

from search import search


def find_rank(case: dict, results: list[dict]) -> int | None:
    """Position (1, 2, 3...) of the first result from the expected section, or None if missing."""
    for position, hit in enumerate(results, start=1):
        same_document = hit["ref"].startswith(case["document"] + "#")
        same_section = case["section"] in hit["section"]
        if same_document and same_section:
            return position
    return None


def main():
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    cases = json.loads(Path("eval_questions.json").read_text(encoding="utf-8"))

    hit_at_1 = 0
    hit_at_k = 0
    reciprocal_ranks = 0.0

    for case in cases:
        results = search(case["question"], top_k=k)
        rank = find_rank(case, results)

        if rank == 1:
            hit_at_1 += 1
        if rank is not None:
            hit_at_k += 1
            reciprocal_ranks += 1 / rank

        label = "OK  " if rank == 1 else (f"#{rank}  " if rank else "MISS")
        print(f"{label} {case['question']}")
        if rank != 1:
            top = results[0]
            print(f"       top result was: {top['ref']} \"{top['section']}\" ({top['score']})")

    n = len(cases)
    print(f"\nHit@1 {hit_at_1 / n:.2f} | Hit@{k} {hit_at_k / n:.2f} | MRR {reciprocal_ranks / n:.2f} | {n} questions")


if __name__ == "__main__":
    main()