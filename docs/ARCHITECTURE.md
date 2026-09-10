# Architecture

```text
                 POST /v1/documents:ingest
Document ──► chunker ──► OpenAI embeddings ──► Qdrant collection
                                                     │
                                                     ▼
User ──► POST /v1/chat ──► Responses API agent ──► search_knowledge_base tool
                                │                         │
                                └──► calculate tool        └──► embed query → Qdrant
                                                                  │
                                                                  ▼
                                                           cited final answer
```

## Design choices

- **OpenAI Responses API** is the LLM boundary. The agent uses explicit, strict function schemas and a capped loop.
- **`text-embedding-3-small`** is configured separately from the chat model, so retrieval cost and answer quality can evolve independently.
- **Qdrant** is the vector database. Its collection dimension is configured to match the embedding model. Changing embedding models requires a new collection/re-index.
- **The API attaches citations from retrieval**, rather than trusting a model to manufacture them.
- **The evaluation score is citation recall**, a deterministic first gate that can run in CI. Extend it with answer quality and groundedness judgments before production.

## Production hardening next

1. Put document ingestion on a queue; parse PDF/DOCX in an isolated worker.
2. Add tenant IDs as mandatory payload fields and Qdrant filters before multi-tenant use.
3. Authenticate requests, rate-limit by principal, and emit structured traces/metrics.
4. Add a reranker, retrieval thresholds, and human-reviewed evaluation datasets.
5. Keep the OpenAI key only in a secret manager; never log prompts, keys, or raw tool outputs indiscriminately.

