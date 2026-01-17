from pypdf import PdfReader
import os
import re

def extract_and_chunk_pdf(pdf_path, output_dir, file_prefix, max_chunk_size_bytes=900000):
    """
    Extracts text from a PDF and splits it into text files based on size,
    respecting paragraph boundaries.

    :param pdf_path: Path to the large PDF file.
    :param output_dir: Folder to save the chunked .txt files.
    :param file_prefix: A prefix for the output files.
    :param max_chunk_size_bytes: Max size in bytes for each chunk. 
                                 Set to ~900KB to be safely under the 1MB limit.
    """
    
    print(f"--- Starting processing for: {pdf_path} ---")
    
    # 1. Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # 2. Extract all text using pypdf
    full_text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
        print(f"Successfully extracted text. Total length: {len(full_text)} characters.")
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return

    # 3. Basic text cleaning
    # Normalize excessive newlines - crucial for paragraph splitting
    full_text = re.sub(r'(\n\s*){3,}', '\n\n', full_text)
    # Attempt to fix words broken by hyphenation at the end of a line
    full_text = re.sub(r'-\n', '', full_text)

    # 4. Chunk the text
    # We split by paragraphs (double newlines) and re-combine them.
    paragraphs = full_text.split('\n\n')
    
    current_chunk = ""
    chunk_count = 1
    files_created = []

    for para in paragraphs:
        # Add the paragraph and a newline separator
        para_with_newline = para + "\n\n"
        
        # Check if adding this paragraph *in bytes* exceeds the limit
        if len(current_chunk.encode('utf-8')) + len(para_with_newline.encode('utf-8')) > max_chunk_size_bytes:
            # If it does, save the current chunk to a file
            if current_chunk.strip(): # Ensure chunk isn't empty
                file_name = f"{file_prefix}_chunk_{chunk_count:04d}.txt"
                file_path = os.path.join(output_dir, file_name)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(current_chunk)
                files_created.append(file_name)
                
                chunk_count += 1
                current_chunk = para_with_newline # Start new chunk
            else:
                # This paragraph alone is too big. We have to split it.
                # This is a fallback and is less ideal.
                print(f"Warning: Single paragraph larger than chunk size. Splitting mid-paragraph.")
                current_chunk = para_with_newline
                
        else:
            # If it fits, add it to the current chunk
            current_chunk += para_with_newline

    # 5. Save the last remaining chunk
    if current_chunk.strip():
        file_name = f"{file_prefix}_chunk_{chunk_count:04d}.txt"
        file_path = os.path.join(output_dir, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(current_chunk)
        files_created.append(file_name)

    print(f"--- Finished. Created {len(files_created)} chunk files in '{output_dir}'. ---")


# --- HOW TO USE THE SCRIPT ---
# Example:
pdf_files_to_process = [
    "books/PHB_2014_OCR.pdf",
    # Add other OCR'd PDF files here as they are created
]
output_folder = "dnd_chunks"

for pdf_file in pdf_files_to_process:
    if os.path.exists(pdf_file):
        # Create a prefix based on the PDF filename
        prefix = os.path.splitext(os.path.basename(pdf_file))[0].lower().replace(' ', '_').replace('-', '_')
        extract_and_chunk_pdf(
            pdf_path=pdf_file, 
            output_dir=output_folder,
            file_prefix=prefix
        )
    else:
        print(f"File not found: {pdf_file}")