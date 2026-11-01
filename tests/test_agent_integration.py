"""Offline plumbing verification: scripted model, real SDK runner, real MCP process.

This deliberately does NOT claim to verify natural-language model routing.
"""

import json

import pytest
from agents import Runner, set_tracing_disabled
from agents.items import ModelResponse
from agents.models.interface import Model
from agents.usage import Usage
from openai.types.responses import ResponseFunctionToolCall, ResponseOutputMessage

from campus_library.agent import connect_server, is_error, make_agent


class ScriptedModel(Model):
    """Emit one tool request, verify its actual returned output, then finish."""

    def __init__(self, tool_name, arguments, expected_fragment):
        self.tool_name = tool_name
        self.arguments = arguments
        self.expected_fragment = expected_fragment
        self.turn = 0
        self.received_tool_output = False

    async def get_response(self, *args, **kwargs):
        self.turn += 1
        inputs = kwargs.get("input", args[1] if len(args) > 1 else [])
        if self.turn == 1:
            output = ResponseFunctionToolCall(
                id="fc_scripted", call_id="call_scripted", type="function_call",
                name=self.tool_name, arguments=json.dumps(self.arguments),
            )
        else:
            assert self.turn == 2, "Unexpected extra model turn"
            serialized = json.dumps(inputs, default=str)
            assert "function_call_output" in serialized
            assert self.expected_fragment in serialized
            self.received_tool_output = True
            output = ResponseOutputMessage(
                id="msg_scripted", type="message", role="assistant", status="completed",
                content=[{"type": "output_text", "text": "Scripted SDK round trip verified.", "annotations": []}],
            )
        return ModelResponse(output=[output], usage=Usage(), response_id=f"offline-{self.turn}")

    async def stream_response(self, *args, **kwargs):
        raise NotImplementedError("This offline test uses the non-streaming Runner.")
        yield  # pragma: no cover - satisfy the abstract async iterator contract


@pytest.mark.parametrize("tool, arguments, fragment, expected_error", [
    ("search_catalog", {"query": "python"}, "B001", False),
    ("create_hold", {"book_id": "B001", "student_id": "S1001"}, "created", False),
    ("reserve_book", {"query": "agentic", "student_id": "S1001"}, "B002", False),
    ("create_hold", {"book_id": "B003", "student_id": "S1002"}, "BOOK_UNAVAILABLE", True),
])
async def test_runner_mcp_roundtrip(tmp_path, tool, arguments, fragment, expected_error):
    set_tracing_disabled(True)
    model = ScriptedModel(tool, arguments, fragment)
    async with connect_server(tmp_path / "agent.sqlite3") as server:
        result = await Runner.run(make_agent(server, model=model), "Offline scripted integration check.", max_turns=3)
        assert result.final_output == "Scripted SDK round trip verified."
        assert model.received_tool_output
        assert len(server.calls) == 1
        assert server.calls[0]["tool"] == tool
        assert server.calls[0]["arguments"] == arguments
        data = server.calls[0]["result"]
        assert bool(data.get("isError", data.get("is_error", False))) == expected_error
