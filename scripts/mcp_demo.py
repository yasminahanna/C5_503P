"""A real stdio MCP check without an LLM or API key. Not the live-agent video."""

import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from agents import set_tracing_disabled

from campus_library.agent import connect_server, is_error


async def check(db: Path) -> None:
    async with connect_server(db) as server:
        tools = await server.list_tools()
        assert {t.name for t in tools} == {"search_catalog", "create_hold", "reserve_book"}
        print("Exactly three tools discovered:", ", ".join(t.name for t in tools))
        for tool in tools:
            print(f"\n{tool.name} input schema:")
            schema = getattr(tool, "inputSchema", None) or getattr(tool, "input_schema", None)
            print(json.dumps(schema, indent=2))
        cases = [
            ("search_catalog", {"query": "python"}, False),
            ("create_hold", {"book_id": "B001", "student_id": "S1001"}, False),
            ("reserve_book", {"query": "agentic systems", "student_id": "S1001"}, False),
            ("create_hold", {"book_id": "B003", "student_id": "S1002"}, True),
            ("search_catalog", {"query": "   "}, True),
            ("reserve_book", {"query": "quantum gardening", "student_id": "S1001"}, True),
        ]
        for name, arguments, expected_error in cases:
            result = await server.call_tool(name, arguments)
            assert is_error(result) == expected_error, (name, "unexpected error state")
        print("\nPASS: tool discovery, all three tools, and three predictable errors over stdio.")


def main() -> None:
    set_tracing_disabled(True)
    print("PROTOCOL CHECK ONLY: real MCP, deterministic calls, no LLM/API request.")
    with TemporaryDirectory(prefix="campus-library-check-") as folder:
        asyncio.run(check(Path(folder) / "library.sqlite3"))


if __name__ == "__main__":
    main()
