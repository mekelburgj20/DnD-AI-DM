import sys
import os
import json
import logging
from flask import Flask, request, jsonify, Response

# --- Setup Paths and Logging ---
import logging
logging.basicConfig(filename='mcp_server_http.log', level=logging.INFO, filemode='w')

# --- Import RAG Components ---
# We will load these later inside the server context
from rag_pipeline import EMBEDDING_MODEL
from sentence_transformers import SentenceTransformer
import faiss
import pickle

# --- Global Variables for RAG Artifacts ---
# These will be loaded once when the server starts.
model = None
index = None
chunks = None

# --- Flask App Definition ---
app = Flask(__name__)

def load_rag_artifacts():
    """Loads the RAG artifacts into the global variables."""
    global model, index, chunks
    
    if index is not None: # Already loaded
        return

    try:
        logging.info("Loading RAG artifacts for HTTP server...")
        from rag_pipeline import INDEX_FILE_PATH, CHUNKS_FILE_PATH
        
        index = faiss.read_index(INDEX_FILE_PATH)
        with open(CHUNKS_FILE_PATH, "rb") as f:
            chunks = pickle.load(f)
        
        model = SentenceTransformer(EMBEDDING_MODEL)
        
        logging.info("Successfully loaded all RAG artifacts.")
    except Exception as e:
        logging.error(f"FATAL: Could not load RAG artifacts. Server will not be functional. Error: {e}", exc_info=True)
        # In a real app, you might want to exit or have a health check endpoint report this.

def search(query, k=5):
    """Performs a search using the pre-loaded global artifacts."""
    if not all([model, index, chunks]):
        raise RuntimeError("RAG artifacts are not loaded.")
        
    query_embedding = model.encode([query])
    distances, indices = index.search(query_embedding.astype('float32'), k)
    
    if not indices.size:
        return []
        
    return [chunks[i] for i in indices[0]]

@app.before_request
def ensure_artifacts_loaded():
    """A Flask hook to ensure artifacts are loaded before the first request."""
    load_rag_artifacts()

@app.route('/mcp', methods=['POST'])
def handle_mcp_request():
    """Handles all incoming JSON-RPC requests."""
    req_data = request.get_json()
    method = req_data.get("method")
    params = req_data.get("params", {})
    req_id = req_data.get("id")

    logging.info(f"Received HTTP request (ID: {req_id}): {req_data}")

    if method == 'initialize' or method == 'mcp/discover':
        response_data = {
            "protocolVersion": params.get("protocolVersion", "0.2.0"),
            "serverInfo": {"name": "dnd-rag-http-server", "version": "1.0.0"},
            "capabilities": {
                "tools": {
                    "query_dnd_books": {
                        "description": "Searches the local D&D book library to find relevant information.",
                        "input_schema": {
                            "type": "object",
                            "properties": {"query": {"type": "string"}},
                            "required": ["query"]
                        }
                    }
                }
            }
        }
        return jsonify({"jsonrpc": "2.0", "id": req_id, "result": response_data})

    elif method == 'query_dnd_books':
        query = params.get('query')
        if not query:
            return jsonify({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": "Invalid params: 'query' is required."}})
        
        try:
            results = search(query)
            response_content = {
                "content": [{"type": "text", "text": json.dumps(results, indent=2)}]
            }
            return jsonify({"jsonrpc": "2.0", "id": req_id, "result": response_content})
        except Exception as e:
            logging.error(f"Error during search: {e}", exc_info=True)
            return jsonify({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": f"Internal search error: {e}"}})

    else:
        return jsonify({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}})

if __name__ == '__main__':
    from waitress import serve
    # We no longer load artifacts here. The @app.before_request hook will handle it.
    # This allows the server to start instantly and respond to the handshake.
    logging.info("Starting production server with waitress...")
    serve(app, host='127.0.0.1', port=5001)
