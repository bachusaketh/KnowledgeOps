from typing import Any, Literal

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    text: str = Field(min_length=1, description="Plain-text document content to index.")
    source: str = Field(min_length=1, examples=["employee-handbook.md"])
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    document_id: str
    chunks_indexed: int
    source: str


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=10_000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10_000)
    conversation: list[ConversationMessage] = Field(default_factory=list, max_length=12)


class Citation(BaseModel):
    source: str
    chunk_id: str
    score: float
    excerpt: str


class ToolTrace(BaseModel):
    name: str
    arguments: dict[str, Any]


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    tools_used: list[ToolTrace]
    model: str

