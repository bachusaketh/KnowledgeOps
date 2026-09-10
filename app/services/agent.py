import json
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from app.config import Settings
from app.schemas import Citation, ConversationMessage, ToolTrace
from app.services.tools import TOOL_DEFINITIONS, ToolRegistry


SYSTEM_INSTRUCTIONS = """You are KnowledgeOps Copilot, a careful assistant for an internal knowledge base.
Use search_knowledge_base before answering questions about supplied documents. Ground document claims in
retrieved evidence, state when evidence is absent, and never invent a source. Use calculate for exact arithmetic.
Keep final answers concise and helpful; citations are attached by the application."""


@dataclass
class AgentAnswer:
    answer: str
    citations: list[Citation]
    tools_used: list[ToolTrace]


class ToolCallingAgent:
    """A bounded, observable Responses API tool loop.

    The model chooses a tool; this class validates/executes it and returns the result to the model. The loop is
    capped so a malformed prompt cannot create an unbounded chain of model calls.
    """

    def __init__(self, settings: Settings, tools: ToolRegistry) -> None:
        self._client = OpenAI(api_key=settings.require_openai_key())
        self._settings = settings
        self._tools = tools

    def answer(self, question: str, conversation: list[ConversationMessage]) -> AgentAnswer:
        input_items: list[Any] = [
            {"role": message.role, "content": message.content} for message in conversation
        ]
        input_items.append({"role": "user", "content": question})
        citations: list[Citation] = []
        traces: list[ToolTrace] = []

        for _ in range(self._settings.max_agent_turns):
            response = self._client.responses.create(
                model=self._settings.chat_model,
                instructions=SYSTEM_INSTRUCTIONS,
                input=input_items,
                tools=TOOL_DEFINITIONS,
                parallel_tool_calls=False,
                store=False,
            )
            calls = [item for item in response.output if item.type == "function_call"]
            if not calls:
                return AgentAnswer(
                    answer=response.output_text or "I could not produce an answer.",
                    citations=_deduplicate_citations(citations),
                    tools_used=traces,
                )

            # The model output is included as context so this works with store=False.
            input_items.extend(response.output)
            for call in calls:
                try:
                    arguments = json.loads(call.arguments)
                    tool_result = self._tools.execute(call.name, arguments)
                    citations.extend(tool_result.citations)
                    traces.append(tool_result.trace)
                    output = tool_result.output
                except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                    output = json.dumps({"error": f"Tool execution failed: {exc}"})
                    traces.append(ToolTrace(name=call.name, arguments={}))
                input_items.append({"type": "function_call_output", "call_id": call.call_id, "output": output})

        return AgentAnswer(
            answer="I reached the tool-call limit before completing this request. Please try a narrower question.",
            citations=_deduplicate_citations(citations),
            tools_used=traces,
        )


def _deduplicate_citations(citations: list[Citation]) -> list[Citation]:
    unique: dict[str, Citation] = {}
    for citation in citations:
        unique.setdefault(citation.chunk_id, citation)
    return list(unique.values())

