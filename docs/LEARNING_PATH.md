# Skill map and build order

| Stage | What to learn in this project | Concrete evidence |
| --- | --- | --- |
| 1 | LLM API | `ToolCallingAgent` calls the Responses API. |
| 2 | Embeddings + Vector DB | `OpenAIEmbedder` stores chunk vectors in Qdrant. |
| 3 | RAG | `search_knowledge_base` retrieves evidence at answer time. |
| 4 | Tool calling | Strict JSON schemas plus validated execution in `ToolRegistry`. |
| 5 | Agent | Bounded plan/act/observe loop with tool traces. |
| 6 | Evaluation | JSONL benchmark measures citation recall and latency. |
| 7 | FastAPI | Typed ingestion/chat APIs and OpenAPI docs at `/docs`. |
| 8 | Docker | One-command API + vector DB local stack. |
| 9 | AWS | Terraform provisions ECR, ECS/Fargate, ALB, logs, and secret injection. |

Recommended sequence: run locally, replace the seed document with a domain you understand, add 20 evaluation cases, tune chunking/retrieval, then deploy. The best portfolio story is the measurable improvement you make on a real evaluation set, not the number of services involved.

