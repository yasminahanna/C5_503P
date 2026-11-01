# Verification evidence

This file records results from the executed verification commands. Tests and the protocol demo run without an OpenAI API key. The protocol demo uses the real SDK MCP client and a real FastMCP subprocess.

The scripted-model integration test verifies the Agents SDK runner's plumbing with deterministic model responses. A separate live run now verifies the four recording scenarios with the configured OpenAI model; its actual prompts, MCP calls, results, and answers are in `live_agent_results.json`.

## Recorded local results

- Python: 3.14 on Windows.
- FastMCP: 4.1.4; OpenAI Agents SDK: 0.24.0.
- Test run: **23 passed in 24.10s**.
- Real stdio protocol check: **PASS**, exactly three tools discovered, all three success cases and all three failure cases behaved as expected.
- The four SDK runner integration cases used a scripted model with a real FastMCP subprocess: Data, Action, Orchestration, and unavailable-book error.
- Live model verification: **PASS**, all four scenarios using `gpt-4.1-mini`: catalog lookup, direct hold, orchestrated reservation, and unavailable-book error. Actual calls matched the expected tool for each request, and the assistant explained the final failure without substituting another book.

The test run used `python -m pytest -q --basetemp .runtime/pytest-run-2`, with workspace-local TEMP/TMP paths because this execution environment restricts the default Windows temporary directory. The protocol check used `python -m scripts.mcp_demo` under the same environment. A standard local setup can use the commands in the README.

The live verification used `python -m scripts.live_check`. It made real API calls and used a fresh temporary database. This verifies the four concrete prompts, not routing accuracy across arbitrary requests. The final screencast still needs to be recorded.
