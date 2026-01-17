import fitz  # PyMuPDF
import os

def extract_text_from_pdf(pdf_path, output_txt_path):
    """
    Extracts text from a PDF and saves it to a text file.

    Args:
        pdf_path (str): The path to the input PDF file.
        output_txt_path (str): The path to the output text file.
    """
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        
        with open(output_txt_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(text)
            
        doc.close()
        print(f"Successfully extracted text from '{os.path.basename(pdf_path)}' and saved to '{os.path.basename(output_txt_path)}'")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    pdf_file = r"C:\dnd\books\Dungeon Master's Guide 2024.pdf"
    output_file = r"C:\dnd\books\Dungeon Master's Guide 2024.txt"
    
    extract_text_from_pdf(pdf_file, output_file)