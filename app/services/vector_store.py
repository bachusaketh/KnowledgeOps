from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import Settings


@dataclass(frozen=True)
class SearchHit:
    chunk_id: str
    text: str
    source: str
    score: float
    metadata: dict[str, Any]


class QdrantVectorStore:
    """Qdrant implementation of the vector-store boundary used by RAG and tools."""

    def __init__(self, settings: Settings) -> None:
        api_key = settings.qdrant_api_key.get_secret_value() if settings.qdrant_api_key else None
        self._client = QdrantClient(url=settings.qdrant_url, api_key=api_key, timeout=15)
        self._collection = settings.qdrant_collection
        self._dimensions = settings.embedding_dimensions

    def ensure_collection(self) -> None:
        if self._client.collection_exists(self._collection):
            return
        self._client.create_collection(
            collection_name=self._collection,
            vectors_config=VectorParams(size=self._dimensions, distance=Distance.COSINE),
        )

    def upsert(self, records: list[dict[str, Any]]) -> None:
        if not records:
            return
        self.ensure_collection()
        points = [
            PointStruct(
                id=record["chunk_id"],
                vector=record["embedding"],
                payload={
                    "text": record["text"],
                    "source": record["source"],
                    "document_id": record["document_id"],
                    "chunk_index": record["chunk_index"],
                    "metadata": record["metadata"],
                },
            )
            for record in records
        ]
        self._client.upsert(collection_name=self._collection, points=points, wait=True)

    def search(self, query_vector: list[float], limit: int = 4) -> list[SearchHit]:
        self.ensure_collection()
        results = self._client.query_points(
            collection_name=self._collection,
            query=query_vector,
            limit=limit,
            with_payload=True,
        ).points
        hits: list[SearchHit] = []
        for point in results:
            payload = point.payload or {}
            hits.append(
                SearchHit(
                    chunk_id=str(point.id),
                    text=str(payload.get("text", "")),
                    source=str(payload.get("source", "unknown")),
                    score=float(point.score),
                    metadata=dict(payload.get("metadata", {})),
                )
            )
        return hits

    def is_healthy(self) -> bool:
        try:
            self._client.get_collections()
            return True
        except Exception:  # readiness reporting must not leak infrastructure details
            return False


def new_chunk_id() -> str:
    return str(uuid4())

