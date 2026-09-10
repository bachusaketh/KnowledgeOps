from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration comes only from the environment or an ignored .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "KnowledgeOps Copilot"
    environment: str = "local"
    log_level: str = "INFO"

    openai_api_key: SecretStr | None = None
    chat_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: SecretStr | None = None
    qdrant_collection: str = "knowledgeops"

    chunk_size_words: int = 350
    chunk_overlap_words: int = 60
    max_agent_turns: int = 4

    @field_validator("chunk_overlap_words")
    @classmethod
    def overlap_must_be_smaller_than_chunk(cls, value: int, info) -> int:
        chunk_size = info.data.get("chunk_size_words", 350)
        if value >= chunk_size:
            raise ValueError("CHUNK_OVERLAP_WORDS must be smaller than CHUNK_SIZE_WORDS")
        return value

    def require_openai_key(self) -> str:
        if self.openai_api_key is None:
            raise RuntimeError("OPENAI_API_KEY is required for ingestion and chat.")
        return self.openai_api_key.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    return Settings()

