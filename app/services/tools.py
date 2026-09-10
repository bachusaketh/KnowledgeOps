import ast
import json
import math
from dataclasses import dataclass
from typing import Any

from app.schemas import Citation, ToolTrace
from app.services.embeddings import OpenAIEmbedder
from app.services.vector_store import QdrantVectorStore


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "name": "search_knowledge_base",
        "description": "Search indexed documents for evidence relevant to the user's question.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Focused semantic search query."},
                "max_results": {"type": "integer", "minimum": 1, "maximum": 8},
            },
            "required": ["query", "max_results"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "calculate",
        "description": "Evaluate a simple arithmetic expression when an exact calculation is needed.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "Arithmetic only."}},
            "required": ["expression"],
            "additionalProperties": False,
        },
    },
]


_ALLOWED_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.USub,
    ast.UAdd,
    ast.Constant,
)


def calculate(expression: str) -> float | int:
    """Evaluate arithmetic without exposing Python names, calls, or attribute access."""
    if len(expression) > 200:
        raise ValueError("Expression is too long")
    tree = ast.parse(expression, mode="eval")
    if not all(isinstance(node, _ALLOWED_NODES) for node in ast.walk(tree)):
        raise ValueError("Only arithmetic operators and numbers are allowed")
    result = eval(compile(tree, "<calculation>", "eval"), {"__builtins__": {}}, {})  # noqa: S307
    if not isinstance(result, (int, float)) or isinstance(result, bool) or not math.isfinite(result):
        raise ValueError("Calculation must result in a finite number")
    return result


@dataclass
class ToolResult:
    output: str
    citations: list[Citation]
    trace: ToolTrace


class ToolRegistry:
    def __init__(self, embedder: OpenAIEmbedder, vector_store: QdrantVectorStore) -> None:
        self._embedder = embedder
        self._vector_store = vector_store

    def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        if name == "search_knowledge_base":
            query = str(arguments["query"])
            max_results = min(max(int(arguments["max_results"]), 1), 8)
            query_vector = self._embedder.embed_many([query])[0]
            hits = self._vector_store.search(query_vector, limit=max_results)
            citations = [
                Citation(
                    source=hit.source,
                    chunk_id=hit.chunk_id,
                    score=round(hit.score, 4),
                    excerpt=hit.text[:280],
                )
                for hit in hits
            ]
            output = json.dumps(
                [
                    {"source": hit.source, "chunk_id": hit.chunk_id, "score": hit.score, "text": hit.text}
                    for hit in hits
                ]
            )
            return ToolResult(output=output, citations=citations, trace=ToolTrace(name=name, arguments=arguments))

        if name == "calculate":
            result = calculate(str(arguments["expression"]))
            return ToolResult(
                output=json.dumps({"result": result}),
                citations=[],
                trace=ToolTrace(name=name, arguments=arguments),
            )

        raise ValueError(f"Unknown tool requested: {name}")

