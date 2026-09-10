from typing import Any
from uuid import uuid4

from app.config import Settings
from app.services.embeddings import OpenAIEmbedder
from app.services.vector_store import QdrantVectorStore, new_chunk_id


def chunk_text(text: str, chunk_size_words: int, overlap_words: int) -> list[str]:
    """Create deterministic, overlapping word chunks suitable for a first RAG system."""
    words = text.split()
    if not words:
        return []
    if overlap_words >= chunk_size_words:
        raise ValueError("overlap_words must be smaller than chunk_size_words")

    step = chunk_size_words - overlap_words
    return [
        " ".join(words[start : start + chunk_size_words])
        for start in range(0, len(words), step)
        if words[start : start + chunk_size_words]
    ]


class IngestionService:
    def __init__(self, settings: Settings, embedder: OpenAIEmbedder, vector_store: QdrantVectorStore) -> None:
        self._settings = settings
        self._embedder = embedder
        self._vector_store = vector_store

    def ingest(self, text: str, source: str, metadata: dict[str, Any]) -> tuple[str, int]:
        chunks = chunk_text(
            text,
            chunk_size_words=self._settings.chunk_size_words,
            overlap_words=self._settings.chunk_overlap_words,
        )
        if not chunks:
            raise ValueError("Document contains no indexable text")

        document_id = str(uuid4())
        # Batching is intentional: embedding APIs are much more efficient than one request per chunk.
        embeddings: list[list[float]] = []
        batch_size = 64
        for start in range(0, len(chunks), batch_size):
            embeddings.extend(self._embedder.embed_many(chunks[start : start + batch_size]))

        records = [
            {
                "chunk_id": new_chunk_id(),
                "document_id": document_id,
                "chunk_index": index,
                "text": chunk,
                "source": source,
                "metadata": metadata,
                "embedding": embeddings[index],
            }
            for index, chunk in enumerate(chunks)
        ]
        self._vector_store.upsert(records)
        return document_id, len(records)

