import math

import ollama

MODEL = "qwen3-embedding:0.6b"

sentences = [
    "How long does the battery take to charge?",        # a question
    "A full charge from empty takes about 4.5 hours.",
    "Charging takes roughly four and a half hours.",  # the answer, with different words
    "The football match ended 2-1 after extra time.",
    "How long does the battery take to charge?"   # unrelated
]

def cosine_similarity(a: list[float], b: list[float]) -> float:
    """How much two vectors point in the same direction: 1 = same, 0 = unrelated."""
    dot = sum(x * y for x, y in zip(a, b))
    length_a = math.sqrt(sum(x * x for x in a))
    length_b = math.sqrt(sum(x * x for x in b))
    return dot / (length_a * length_b)

def main():
    response = ollama.embed(model=MODEL, input=sentences)
    vectors = response.embeddings
    print(f"{len(vectors)} vectors, each with {len(vectors[0])} numbers")
    print("First 5 numbers of the question:", [round(x, 4) for x in vectors[0][:5]])
    print("\nSimilarity to the question:")
    question = vectors[0]
    for sentence, vector in zip(sentences[1:], vectors[1:]):
        print(f"  {cosine_similarity(question, vector):.3f}  {sentence}")

if __name__=="__main__":
    main()
    
