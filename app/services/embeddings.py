from openai import OpenAI

from app.config import Settings


class OpenAIEmbedder:
    """Thin adapter so embedding providers can be swapped independently of retrieval."""

    def __init__(self, settings: Settings) -> None:
        self._client = OpenAI(api_key=settings.require_openai_key())
        self._model = settings.embedding_model

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in response.data]

