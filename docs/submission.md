# C5 submission - Yasmina Hanna

**Project:** Campus Library MCP Toolkit  
**Course:** EECE 503P/798S: Agentic Systems

**Code repository URL:** TO FILL AFTER UPLOADING SOURCE  
**Screencast URL:** TO FILL AFTER RECORDING AND UPLOADING VIDEO

## Included deliverables

- Written summary: `docs/written_summary.md` (300-400 words, references outside count).
- FastMCP server: `campus_library/server.py` (exactly three tools).
- OpenAI Agents SDK host/client: `campus_library/agent.py`.
- Typed outputs and shared logic: `campus_library/models.py`, `campus_library/service.py`.
- Setup and configuration: `README.md`, `.env.example`, `requirements.txt`, `requirements-lock.txt`.
- Tests and examples: `tests/`, `scripts/mcp_demo.py`, and local verification evidence.
- Reflection: `docs/reflection.md` (two paragraphs).
- Recording support: `docs/speaker_notes.md`, plus printable PDF and editable Word notes.

## Steps that require your account or recording

1. The live agent has passed all four recording scenarios with your configured API key. Keep the key private in `.env` and rehearse `python -m campus_library.agent --demo` in the installed environment.
2. Record a 5-7 minute screencast showing the **live OpenAI-backed agent**, all three tools, their round trips, and one failure case.
3. Create a GitHub repository (or equivalent) and upload the project source. Exclude `.env`, `.tools`, `.venv`, caches, and local databases; `.gitignore` lists these paths. Use the prepared ZIP as the clean source package.
4. Upload the recording to a platform of your choice and set instructor-accessible permissions.
5. Replace the two URL fields above and submit them together with the written summary, source, and reflection.

Do not submit the protocol check as evidence of real-model routing. The remaining URL fields are intentional: neither a repository URL nor a video URL has been invented.
