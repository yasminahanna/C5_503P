# MCP reading and server exploration

**Yasmina Hanna | EECE 503P/798S: Agentic Systems | C5 - Agent Tools**

**Summary word count: 347 (excluding citations and references).**

The Hugging Face article presents MCP as an open standard for connecting AI assistants to external information and capabilities. Its central problem is integration: a model's training knowledge alone cannot supply current documents, private records, or actions inside another system. Individually written connectors become difficult to maintain as applications and data sources multiply. MCP offers a common interface that allows compatible assistants to discover and use server capabilities, making context integration more reusable. [1]

The architecture separates three responsibilities. The host is the AI application that manages the user interaction and model workflow. An MCP client is the protocol component inside that host that communicates with a particular server; a host can manage multiple clients. The server exposes capabilities over that connection. Tools represent callable operations, resources expose contextual data, and prompts supply reusable interaction templates. The protocol standardizes communication and capability discovery; the host still decides how to incorporate results into the conversation. For precise role definitions, I supplemented the article with the official MCP architecture documentation. [2]

I explored the reference Fetch MCP server's README and Python implementation. Its main tool, `fetch`, retrieves one URL and normally converts HTML into readable Markdown. Its arguments include the URL, maximum response length, starting character index, and a raw-content option. These parameters describe one retrieval operation rather than unrelated modes such as fetching, editing files, and sending messages. Bounded output and continuation offsets help an agent work within its context budget. The README documents the arguments and deployment options, making the interface understandable before execution. [3]

The implementation also validates inputs and reports retrieval failures rather than silently returning success. Internally, networking, access checks, conversion, and truncation are separate concerns supporting one externally meaningful result. That is a reasonable single-purpose boundary: implementation complexity does not automatically make a tool multipurpose. My critique is that textual page output is less structured than a typed result containing separate content and pagination fields. Network availability and changing pages also limit repeatability. For my toolkit, I therefore use typed outputs, explicit failure codes, stable selection rules, and a local catalog so the demonstration remains predictable. [4]

## References

1. Ksenia Se, [What Is MCP, and Why Is Everyone Suddenly Talking About It?](https://huggingface.co/blog/Kseniase/mcp), Hugging Face, March 17, 2025.
2. Model Context Protocol, [Architecture overview](https://modelcontextprotocol.io/docs/learn/architecture).
3. Model Context Protocol reference servers, [Fetch README](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch).
4. Model Context Protocol reference servers, [Fetch Python implementation](https://github.com/modelcontextprotocol/servers/blob/main/src/fetch/src/mcp_server_fetch/server.py).

Reading note: the Hugging Face page links to a longer Turing Post article. The summary above distinguishes the accessible Hugging Face discussion from the official architecture reference and the implementation I inspected. Word count applies to the four summary paragraphs, excluding heading, citation markers, references, and this note.
