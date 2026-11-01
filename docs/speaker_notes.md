# Video speaker notes

**Yasmina Hanna | Campus Library MCP Toolkit | C5 - Agent Tools**  
**Target length:** approximately 6 minutes, including tool execution and screen transitions.  
**Format:** read the narration aloud; the screen cues and commands are for you, not spoken text.

## Before recording

1. Follow the README setup, put your own key in `.env`, and rehearse the live demo once. Keep `.env` closed during the recording.
2. Open the project in your editor with `README.md`, `campus_library/server.py`, `campus_library/service.py`, `campus_library/agent.py`, and `docs/reflection.md` ready in tabs.
3. Open a terminal in the project root. Increase the font size so JSON results are readable. Hide unrelated windows and notifications.
4. Have the repository page ready after you upload the source. Record your actual repository URL; do not read a placeholder as if it were a published link.
5. Use the Windows commands below. The demo starts a fresh temporary database each time, so rehearsing does not consume the books for the final recording.
6. Speak at roughly 125-140 words per minute. The narration is about 650-750 words; use the remaining time for live calls and pointing. Keep the final video within 5-7 minutes. If API calls are slow, shorten the code tour rather than skipping a tool.

## 0:00-0:40 - Introduction and the three tools

**Screen:** README title and tool-contract table.

**Say:**

Hello, I'm Yasmina Hanna. For this assignment, I built a Campus Library MCP Toolkit using FastMCP and the OpenAI Agents SDK. It works with a small fictional catalog, and its holds are saved in a local SQLite database.

There are exactly three tools. The Data tool, search catalog, looks up books without changing stored data. The Action tool, create hold, saves one reservation for a specific book and student. The Orchestration tool, reserve book, fulfills a topic-based reservation by coordinating the search and hold operations.

## 0:40-1:20 - MCP concepts and existing-server exploration

**Screen:** README architecture diagram, then briefly `docs/written_summary.md` references.

**Say:**

The assigned article explains MCP as a common way to connect assistants to external data and capabilities. In my project, the Python application is the host. Inside it, the SDK's MCP client communicates with a separate FastMCP server process over standard input and output. The server exposes the tool definitions and executes calls; the model chooses which tool to request.

I also explored the reference Fetch server. Its fetch tool has one clear retrieval purpose, with controls for output length and pagination. That influenced my choice to keep interfaces focused and to make outputs and failures predictable.

## 1:20-2:00 - Code and contracts

**Screen:** `server.py` decorators and signatures; briefly show `models.py` and `agent.py`'s `connect_server` / `make_agent`.

**Say:**

Here are the three decorated FastMCP functions. Their descriptions explain when to use them, and typed arguments generate their input schemas. Pydantic models define the structured outputs. A student ID must follow the demo format, such as S1001.

The host uses MCPServerStdio to start the server, attaches it through the agent's MCP servers configuration, and calls Runner dot run. The terminal prints actual MCP requests and responses so we can follow the full round trip. Catalog searches use a read-only connection; hold creation uses a transaction to protect availability.

## 2:00-2:45 - Live Data tool

**Screen action:** start the live demo, then press Enter for scenario 1.

```powershell
.\.venv\Scripts\python.exe -m campus_library.agent --demo
```

**Displayed request:** `Search the catalog for python. Do not reserve anything.`

**Say before pressing Enter:**

Now I will run the live agent. The initial discovery lists exactly three tools. My first request asks for Python books without reserving anything.

**After the result, point to the tool name, arguments, response, and assistant answer. Say:**

Here the agent requested search catalog. The client sent the arguments to the server, and the server returned book B001 with two available copies. The agent then used that result in its answer. This operation only retrieved information.

## 2:45-3:30 - Live Action tool

**Screen action:** press Enter for scenario 2.

**Displayed request:** `Create a hold for book B001 for student S1001.`

**Say:**

Next, I explicitly request a hold for B001 under student S1001. The agent calls create hold with those identifiers.

The response contains a created status and a generated hold identifier. This is a persistent local database change, not just a sentence saying that a reservation happened. Repeating the same book and student pair returns the existing hold instead of consuming another copy. The effect is limited to this demonstration database.

## 3:30-4:25 - Live Orchestration tool

**Screen action:** press Enter for scenario 3; keep the `steps` field visible.

**Displayed request:** `Reserve a book about agentic systems for student S1001 using reserve_book.`

**Say:**

For the higher-level request, I ask for an agentic systems book without choosing an identifier. The agent calls reserve book.

Inside the server, orchestration calls the same search implementation used by the Data tool, tries matching titles in book-ID order, and calls the same hold implementation used by the Action tool. It refreshes availability afterward.

The response identifies B002, includes its hold, and lists the internal steps. We see one external MCP call because this composition happens inside the server. The workflow has one clear goal: complete a topic-based reservation.

## 4:25-5:15 - Predictable failure and verification

**Screen action:** press Enter for scenario 4. Point to `BOOK_UNAVAILABLE`, the protocol error indicator, and the assistant's explanation. After the demo, run the tests.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

**Say:**

Now I request a hold for B003, which has no available copies. The server returns BOOK UNAVAILABLE instead of pretending the reservation succeeded. The agent can explain the failure without silently reserving a different book.

My tests cover successful calls, invalid inputs, unavailable books, persistence, duplicate prevention, and competing requests for the last copy. They also check MCP tool discovery and the SDK connection. The automated SDK test uses a scripted model for repeatability; the demonstration we just watched uses the configured OpenAI model.

## 5:15-6:00 - Challenges, reflection, and repository

**Screen:** show `service.py` orchestration briefly, then your actual repository page and reflection.

**Say:**

One design challenge was drawing the boundary around orchestration. I kept catalog retrieval and hold creation independently usable, then reused their implementations for a single reservation workflow. Another challenge was handling retries and concurrent requests. A uniqueness constraint prevents duplicate holds, and a database transaction protects the last available copy.

Three tools are a useful scope for this prototype. A real deployment would need authentication, a real catalog connection, and additional capabilities such as cancellation. I would also evaluate routing with more ambiguous requests.

Here is my code repository. The submission includes the source, setup instructions, tests, reading summary, and reflection, together with the link to this recording. Thank you.

## If the live result differs during rehearsal

- Describe the tool call actually shown. Do not narrate an expected result that is absent.
- If a model answers without a tool, repeat the request with the specific tool name and supplied arguments; inspect the trace and rehearse again before recording.
- If API access fails, resolve the key, quota, model access, or connection first. `python -m scripts.mcp_demo` is a useful protocol check, but it does not satisfy the live-agent recording requirement.
- Hold IDs and timestamps vary; read the actual values on screen only if helpful. B001, B002, and B003 are stable in a fresh demo.
- Do not show an API key or claim a repository/video link exists before you have created it.
