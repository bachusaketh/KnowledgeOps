# KnowledgeOps Copilot

A complete, portfolio-grade backend project for learning **LLM APIs → RAG → embeddings → vector databases → tool calling → agents → evaluation → FastAPI → Docker → AWS**.

It answers questions over documents you ingest. The model decides when to call a semantic-search tool or a safe calculator; the API returns the answer, the actual retrieval citations, and an observable tool trace.

## What is included

- OpenAI Responses API integration for a multi-step tool-calling agent.
- OpenAI embeddings and Qdrant as a real, persistent vector database.
- A complete RAG ingestion/retrieval path with deterministic overlapping chunks.
- Strict function schemas plus a bounded agent loop and safe arithmetic tool.
- FastAPI endpoints, typed request/response models, readiness probes, and OpenAPI docs.
- Docker Compose for a local API + Qdrant stack.
- A JSONL evaluation set that measures citation recall and latency.
- Terraform for AWS ECR, ECS/Fargate, ALB, CloudWatch Logs, and Secrets Manager injection.

## Run locally

Requirements: Python 3.11+ and Docker Desktop. Create an OpenAI API key, then from the project root:

```powershell
Copy-Item .env.example .env
# Edit .env and set OPENAI_API_KEY
docker compose up --build
```

In another terminal, seed the demo document and ask a question:

```powershell
python examples/seed.py
Invoke-RestMethod -Method Post -Uri http://localhost:8000/v1/chat -ContentType 'application/json' -Body '{"question":"What is the internet reimbursement cap?"}'
```

Open `http://localhost:8000/docs` to try the interactive API. Run the first deterministic evaluation after seeding:

```powershell
python evals/run_evals.py
```

For a non-Docker API workflow, create a virtual environment, run `pip install -e ".[dev]"`, start Qdrant separately, then run `uvicorn app.main:app --reload`.

## API contract

`POST /v1/documents:ingest`

```json
{
  "source": "leave-policy.md",
  "text": "Employees receive 20 paid leave days per calendar year.",
  "metadata": {"department": "People"}
}
```

`POST /v1/chat`

```json
{
  "question": "How many leave days do employees receive?"
}
```

The response includes `answer`, `citations`, `tools_used`, and the configured `model`. Citation metadata comes from Qdrant retrieval, not model-generated URLs.

## Important engineering notes

- `CHAT_MODEL` and `EMBEDDING_MODEL` are configuration, not hard-coded policy. Use models available to your OpenAI project; re-index whenever the embedding model/vector dimension changes.
- The agent passes `store=False` and carries the current tool-call context in-process. Decide your own retention, privacy, and observability policy before handling real user data.
- This starter accepts plain text so the RAG core stays clear. Add hardened PDF/DOCX extraction, malware scanning, authorization, tenant filters, and asynchronous ingestion before production use.
- The calculator blocks names, calls, attributes, and non-finite results. Do not turn it into a general Python execution tool.

## Deployment

Follow [AWS deployment](docs/AWS_DEPLOYMENT.md) for the Terraform-backed Fargate path. See [architecture](docs/ARCHITECTURE.md) for component boundaries and [the skill map](docs/LEARNING_PATH.md) for a staged study plan.

The OpenAI implementation follows the Responses API’s documented model/tool interface: a response can use custom function tools, and the API exposes instructions, tools, and tool choice as first-class inputs. [Official OpenAI API reference](https://developers.openai.com/api/reference/cli/resources/responses/methods/create)

