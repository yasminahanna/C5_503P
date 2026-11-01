"""Verify real model routing through the SDK and MCP, using temporary storage.

Requires the student's configured API key and makes billable model requests.
Writes only tool results and model answers, never credentials.
"""

import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from agents import Runner, set_tracing_disabled
from dotenv import load_dotenv

from campus_library.agent import DEMO_PROMPTS, ROOT, connect_server, make_agent


async def check(database: Path) -> dict:
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "live OpenAI model + Agents SDK + real stdio MCP",
        "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        "scenarios": [],
    }
    expected = ["search_catalog", "create_hold", "reserve_book", "create_hold"]
    async with connect_server(database) as server:
        tools = await server.list_tools()
        report["discovered_tools"] = [t.name for t in tools]
        assert set(report["discovered_tools"]) == {"search_catalog", "create_hold", "reserve_book"}
        agent = make_agent(server)
        history = []
        for index, (prompt, name) in enumerate(zip(DEMO_PROMPTS, expected)):
            start = len(server.calls)
            print(f"\nLIVE SCENARIO {index + 1}: {prompt}", flush=True)
            history.append({"role": "user", "content": prompt})
            result = await Runner.run(agent, history, max_turns=10)
            history = result.to_input_list()
            calls = server.calls[start:]
            assert [c["tool"] for c in calls] == [name], f"Unexpected routing in scenario {index + 1}"
            payload = calls[0]["result"]
            error = bool(payload.get("isError", payload.get("is_error", False)))
            assert error == (index == 3), f"Unexpected error state in scenario {index + 1}"
            if index == 3:
                assert "BOOK_UNAVAILABLE" in json.dumps(payload)
            print(f"ASSISTANT: {result.final_output}", flush=True)
            report["scenarios"].append({
                "prompt": prompt, "calls": calls, "assistant_answer": result.final_output,
                "expected_tool": name, "passed": True,
            })
    report["passed"] = True
    return report


def main() -> None:
    load_dotenv(ROOT / ".env")
    set_tracing_disabled(True)
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise SystemExit("OPENAI_API_KEY is missing. Configure .env privately first.")
    print("API key loaded: yes (value hidden)", flush=True)
    runtime = ROOT / ".runtime"
    runtime.mkdir(exist_ok=True)
    try:
        with TemporaryDirectory(prefix="live-verification-", dir=runtime) as folder:
            report = asyncio.run(check(Path(folder) / "library.sqlite3"))
    except Exception as exc:
        # Exception strings can include request details. Print only safe diagnostics.
        print(f"Live verification failed: {type(exc).__name__}", flush=True)
        status = getattr(exc, "status_code", None)
        if isinstance(status, int):
            print(f"HTTP status: {status}", flush=True)
        code = getattr(exc, "code", None)
        if isinstance(code, str) and code.replace("_", "").isalnum():
            print(f"API error code: {code}", flush=True)
        raise SystemExit(1) from None
    output = ROOT / "verification" / "live_agent_results.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("\nPASS: all four live-agent scenarios. Evidence saved to verification/live_agent_results.json.")


if __name__ == "__main__":
    main()
