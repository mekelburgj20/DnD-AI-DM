import os
import re
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# --- 1. Configuration ---
# The folder containing your source .txt files
SOURCE_DIRECTORY = "books" 
# The directory where we'll save the processed chunks, index, and other artifacts
ARTIFACTS_DIRECTORY = "rag_artifacts" 
# The path for the final, consolidated text file
CONSOLIDATED_FILE_PATH = os.path.join(ARTIFACTS_DIRECTORY, "all_books_consolidated.txt")
# The path for the file containing all the text chunks
CHUNKS_FILE_PATH = os.path.join(ARTIFACTS_DIRECTORY, "text_chunks.pkl")
# The path for the embeddings file
EMBEDDINGS_FILE_PATH = os.path.join(ARTIFACTS_DIRECTORY, "embeddings.pkl")
# The name of the sentence transformer model we'll use for embeddings
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
# The path for the FAISS index file
INDEX_FILE_PATH = os.path.join(ARTIFACTS_DIRECTORY, "faiss_index.idx")
# We define chunk size in terms of tokens, not characters. A good starting point is 512.
CHUNK_SIZE_TOKENS = 512
# Overlap helps maintain context between chunks. 50 tokens is a reasonable overlap.
CHUNK_OVERLAP_TOKENS = 50

# --- Helper Functions for Text Cleaning (inspired by your clean_text.py) ---

def clean_text(text):
    """A more streamlined function to clean the text."""
    # Normalize excessive newlines
    text = re.sub(r'(\n\s*){3,}', '\n\n', text)
    # Fix words broken by hyphenation at the end of a line
    text = re.sub(r'-\n', '', text)
    # Remove space before punctuation
    text = re.sub(r'\s+([.,!?])', r'\1', text)
    # Collapse multiple spaces into one, but not newlines
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text

# --- 2. Document Loading and Chunking ---

def load_and_chunk_documents():
    """
    Loads all .txt files from the source directory, consolidates, cleans,
    and splits them into overlapping chunks.
    """
    print("--- Step 1: Loading and Chunking Documents ---")

    all_text = ""
    print(f"Searching for .txt files in '{SOURCE_DIRECTORY}' and its subdirectories...")
    
    # Walk through the source directory and its subdirectories
    for root, _, files in os.walk(SOURCE_DIRECTORY):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        all_text += f.read() + "\n\n"
                except Exception as e:
                    print(f"Warning: Could not read file {file_path}: {e}")

    print(f"Successfully loaded {len(all_text)} characters from all .txt files.")

    # Clean the consolidated text
    print("Cleaning text...")
    cleaned_text = clean_text(all_text)

    # Save the consolidated text for inspection
    with open(CONSOLIDATED_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(cleaned_text)
    print(f"Saved consolidated and cleaned text to '{CONSOLIDATED_FILE_PATH}'.")

    # Chunk the text
    # A simple way to chunk is by splitting the text and then joining it.
    # We'll use a token-based approach for more meaningful chunks.
    # For simplicity here, we'll use character-based splitting as a proxy.
    # A true token-based approach would use the model's tokenizer.
    # Let's approximate token size as 4 characters.
    char_chunk_size = CHUNK_SIZE_TOKENS * 4
    char_overlap = CHUNK_OVERLAP_TOKENS * 4

    text_chunks = []
    start = 0
    while start < len(cleaned_text):
        end = start + char_chunk_size
        chunk = cleaned_text[start:end]
        text_chunks.append(chunk)
        start += char_chunk_size - char_overlap

    if not text_chunks:
        print("Warning: No text chunks were created. Check your source files.")
        return

    # Save the chunks to a pickle file
    with open(CHUNKS_FILE_PATH, "wb") as f:
        pickle.dump(text_chunks, f)
        
    print(f"Created {len(text_chunks)} chunks and saved them to '{CHUNKS_FILE_PATH}'.")

# --- 3. Embedding Generation ---

def generate_and_save_embeddings():
    """
    Loads the text chunks and uses a sentence-transformer model to create
    vector embeddings for each chunk.
    """
    print("\n--- Step 2: Generating and Saving Embeddings ---")

    # Load the text chunks
    try:
        with open(CHUNKS_FILE_PATH, "rb") as f:
            text_chunks = pickle.load(f)
    except FileNotFoundError:
        print(f"Error: Chunks file not found at '{CHUNKS_FILE_PATH}'.")
        print("Please run Step 1 (load_and_chunk_documents) first.")
        return

    if not text_chunks:
        print("Error: The chunks file is empty. Cannot generate embeddings.")
        return

    # Initialize the sentence transformer model
    print(f"Loading embedding model '{EMBEDDING_MODEL}'...")
    # The model will be downloaded automatically on first use
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("Model loaded.")

    # Generate embeddings for all chunks
    print(f"Generating embeddings for {len(text_chunks)} chunks... (This may take a while)")
    embeddings = model.encode(text_chunks, show_progress_bar=True)
    print("Embeddings generated successfully.")

    # Save the embeddings to a file
    with open(EMBEDDINGS_FILE_PATH, "wb") as f:
        pickle.dump(embeddings, f)
    
    print(f"Embeddings saved to '{EMBEDDINGS_FILE_PATH}'.")

# --- 4. FAISS Index Creation ---

def create_faiss_index():
    """
    Loads the embeddings and builds a FAISS index for efficient similarity searching.
    """
    print("\n--- Step 3: Creating FAISS Index ---")

    # Load the embeddings
    try:
        with open(EMBEDDINGS_FILE_PATH, "rb") as f:
            embeddings = pickle.load(f)
    except FileNotFoundError:
        print(f"Error: Embeddings file not found at '{EMBEDDINGS_FILE_PATH}'.")
        print("Please run Step 2 (generate_and_save_embeddings) first.")
        return

    if embeddings is None or len(embeddings) == 0:
        print("Error: The embeddings file is empty. Cannot create index.")
        return

    # FAISS requires the data to be in a float32 numpy array
    embeddings = np.array(embeddings).astype('float32')

    # Get the dimensionality of the embeddings
    d = embeddings.shape[1]

    # Create the FAISS index
    # IndexFlatL2 is a standard index that performs an exhaustive L2 distance search.
    print(f"Creating FAISS index with dimension {d}...")
    index = faiss.IndexFlatL2(d)

    # Add the embeddings to the index
    index.add(embeddings)

    # Save the index to disk
    faiss.write_index(index, INDEX_FILE_PATH)
    
    print(f"FAISS index created with {index.ntotal} vectors and saved to '{INDEX_FILE_PATH}'.")

# --- 5. Query Engine ---

def search_documents(query, k=5):
    """
    Takes a user query, embeds it, and searches the FAISS index to find
    the top 'k' most relevant text chunks.
    """
    print(f"\n--- Searching for query: '{query}' ---")
    
    # --- Load all necessary artifacts ---
    try:
        # Load the FAISS index
        index = faiss.read_index(INDEX_FILE_PATH)
        
        # Load the text chunks
        with open(CHUNKS_FILE_PATH, "rb") as f:
            text_chunks = pickle.load(f)
            
    except FileNotFoundError as e:
        print(f"Error: Could not load necessary file. {e}")
        print("Please ensure the pipeline has been run fully at least once.")
        return []

    # --- Embed the query ---
    # Initialize the model
    model = SentenceTransformer(EMBEDDING_MODEL)
    # Encode the query and reshape it for FAISS
    query_embedding = model.encode([query]).astype('float32')

    # --- Search the index ---
    # The search function returns distances and indices (D, I)
    distances, indices = index.search(query_embedding, k)

    # --- Retrieve and return the results ---
    # The 'indices' are a 2D array, so we take the first row
    results = [text_chunks[i] for i in indices[0]]
    
    return results


# --- Main Execution Block ---

def ask_llm(query, context):
    """
    (Demonstration Function)
    Constructs a prompt and simulates asking the LLM a question with context.
    """
    
    context_str = "\n\n---\n\n".join(context)
    
    prompt = f"""
Based on the following context from the D&D rulebooks, please provide a comprehensive answer to the user's question.

CONTEXT:
---
{context_str}
---

QUESTION: {query}

ANSWER:
"""
    
    print("\n" + "="*50)
    print("--- PROMPT FOR LLM (SIMULATED) ---")
    print("="*50)
    print(prompt)
    print("="*50)
    print("--- END OF PROMPT ---")
    print("="*50)
    
    # In a real application, you would send this 'prompt' to an LLM API (like Gemini, OpenAI, etc.)
    # and then print the response.
    print("\n[In a real application, the LLM would generate a detailed answer based on the prompt above.]")


def main():
    """Main function to run the RAG pipeline and enter an interactive query loop."""
    
    # --- Check if setup is needed ---
    if not os.path.exists(INDEX_FILE_PATH) or not os.path.exists(CHUNKS_FILE_PATH):
        print("--- No existing index found. Starting one-time RAG Pipeline Setup ---")
        os.makedirs(ARTIFACTS_DIRECTORY, exist_ok=True)
        
        # Step 1: Load and chunk the source documents
        load_and_chunk_documents()
        # Step 2: Generate embeddings for the chunks
        generate_and_save_embeddings()
        # Step 3: Create the search index
        create_faiss_index()
        
        print("\n--- RAG Pipeline Setup Complete ---")
    else:
        print("--- Existing RAG index found. Skipping setup. ---")

    # --- Interactive Query Loop ---
    print("\n--- Starting Interactive D&D Query Session ---")
    print("Enter your question below. Type 'exit' or 'quit' to end the session.")
    
    while True:
        query = input("\nYour Question: ")
        if query.lower() in ['exit', 'quit']:
            print("Exiting query session. Goodbye!")
            break
        
        # 1. Retrieve relevant context
        retrieved_context = search_documents(query)
        
        if not retrieved_context:
            print("Could not find any relevant documents for that query.")
            continue
            
        # 2. (Optional) Print the raw retrieved context for inspection
        # print(f"\nTop {len(retrieved_context)} retrieved chunks for '{query}':")
        # for i, chunk in enumerate(retrieved_context):
        #     print(f"  {i+1}. {chunk[:150].replace('\n', ' ')}...")
            
        # 3. Pass the query and context to the LLM for a final answer
        ask_llm(query, retrieved_context)


if __name__ == "__main__":
    main()