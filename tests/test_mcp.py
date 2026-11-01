import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from campus_library.server import build_server


async def test_exactly_three_typed_tools(tmp_path):
    async with Client(build_server(tmp_path / "test.sqlite3")) as client:
        tools = await client.list_tools()
        assert {t.name for t in tools} == {"search_catalog", "create_hold", "reserve_book"}
        for tool in tools:
            data = tool.model_dump(by_alias=True)
            assert data.get("description")
            assert data.get("inputSchema", data.get("input_schema"))
            assert data.get("outputSchema", data.get("output_schema"))
        # No duplicate lookup exposed as a resource.
        assert await client.list_resources() == []


async def test_all_three_tools_and_errors_through_mcp(tmp_path):
    async with Client(build_server(tmp_path / "test.sqlite3")) as client:
        data = await client.call_tool("search_catalog", {"query": "python"})
        assert "B001" in str(data)
        action = await client.call_tool("create_hold", {"book_id": "B001", "student_id": "S1001"})
        assert "created" in str(action)
        workflow = await client.call_tool("reserve_book", {"query": "agentic", "student_id": "S1001"})
        assert "B002" in str(workflow)
        with pytest.raises(ToolError, match="BOOK_UNAVAILABLE"):
            await client.call_tool("create_hold", {"book_id": "B003", "student_id": "S1002"})
        with pytest.raises(ToolError, match="INVALID_QUERY"):
            await client.call_tool("search_catalog", {"query": "   "})
        with pytest.raises(ToolError, match="NO_MATCH"):
            await client.call_tool("reserve_book", {"query": "unknown", "student_id": "S1001"})


async def test_schema_rejects_invalid_student_id(tmp_path):
    async with Client(build_server(tmp_path / "test.sqlite3")) as client:
        with pytest.raises(ToolError):
            await client.call_tool("create_hold", {"book_id": "B001", "student_id": "wrong"})
