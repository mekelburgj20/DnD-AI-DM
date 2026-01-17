# DnD-AI-DM - RAG Agent MCP Server

An MCP setup to enable an AI agent to DM for a DnD campaign.

This project allows an AI agent to query a local library of D&D books using Retrieval Augmented Generation (RAG). It provides an MCP (Model Context Protocol) compatible HTTP server.

## Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Add Books:**
    Place your D&D source books (PDF or Text) into the `books/` directory.

3.  **Process Data:**
    Run the pipeline to chunk your books and generate the search index.
    ```bash
    python rag_pipeline.py
    ```
    *Note: You may need to use `chunk_pdf.py` first if you only have raw PDFs.*

4.  **Start the Server:**
    ```bash
    python mcp_server.py
    ```
    The server will start on `http://127.0.0.1:5001`.

## MCP Configuration (for KiloCode/Claude)

Add the following to your MCP settings file:

```json
"dnd-rag-server": {
  "command": "python",
  "args": [
    "-u",
    "C:\\path\\to\\your\\dnd-rag-agent\\mcp_server.py"
  ],
  "url": "http://127.0.0.1:5001/mcp"
}
```

## Tools

-   `query_dnd_books(query: str)`: Searches the processed D&D books for relevant information.