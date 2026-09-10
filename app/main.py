import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.schemas import ChatRequest, ChatResponse, IngestRequest, IngestResponse
from app.services.agent import ToolCallingAgent
from app.services.embeddings import OpenAIEmbedder
from app.services.ingestion import IngestionService
from app.services.tools import ToolRegistry
from app.services.vector_store import QdrantVectorStore


@dataclass
class Services:
    ingestion: IngestionService
    agent: ToolCallingAgent
    vector_store: QdrantVectorStore


def build_services(settings: Settings) -> Services:
    embedder = OpenAIEmbedder(settings)
    vector_store = QdrantVectorStore(settings)
    return Services(
        ingestion=IngestionService(settings, embedder, vector_store),
        agent=ToolCallingAgent(settings, ToolRegistry(embedder, vector_store)),
        vector_store=vector_store,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    app.state.services = build_services(settings)
    yield


app = FastAPI(
    title="KnowledgeOps Copilot API",
    version="0.1.0",
    description="RAG + embeddings + Qdrant + tool-calling agent reference project.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def services_for(request: Request) -> Services:
    return request.app.state.services


def service_error(exc: Exception) -> HTTPException:
    logging.exception("Request failed", exc_info=exc)
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@app.get("/healthz", tags=["operations"])
def healthz() -> dict[str, str]:
    """Liveness probe: does not require a network dependency."""
    return {"status": "ok"}


@app.get("/readyz", tags=["operations"])
def readyz(request: Request) -> dict[str, str]:
    if not services_for(request).vector_store.is_healthy():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Vector store unavailable")
    return {"status": "ready"}


@app.post("/v1/documents:ingest", response_model=IngestResponse, tags=["knowledge"])
def ingest_document(payload: IngestRequest, request: Request) -> IngestResponse:
    try:
        document_id, chunks_indexed = services_for(request).ingestion.ingest(
            payload.text, payload.source, payload.metadata
        )
        return IngestResponse(
            document_id=document_id, chunks_indexed=chunks_indexed, source=payload.source
        )
    except (RuntimeError, ValueError) as exc:
        raise service_error(exc) from exc


@app.post("/v1/chat", response_model=ChatResponse, tags=["agent"])
def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    try:
        result = services_for(request).agent.answer(payload.question, payload.conversation)
        return ChatResponse(
            answer=result.answer,
            citations=result.citations,
            tools_used=result.tools_used,
            model=get_settings().chat_model,
        )
    except RuntimeError as exc:
        raise service_error(exc) from exc

