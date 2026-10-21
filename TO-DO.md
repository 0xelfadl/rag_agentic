# Hybrid search (vector + keyword) fixes E12 miss, because keyword search matches “E12” exactly. It’s pure Postgres (full-text search + a smart way to merge the two rankings).

## Reranking fixes“stuck in Eco” miss: a second model reads the question and each candidate together and re-orders the top results.

### Harder eval + multi-step tools: add tricky questions that fail sometimes, and give the agent a read_section tool to read the chunks around a hit.