import re

def clean_dnd_text(input_file_path, output_file_path):
    """
    Cleans up a text file extracted from a D&D PDF.
    - Joins lines that seem to be part of the same paragraph.
    - Removes extra whitespace.
    - Attempts to fix words split across lines.
    """
    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        cleaned_lines = []
        buffer = ""

        for i, line in enumerate(lines):
            line = line.strip()

            if not line:
                if buffer:
                    cleaned_lines.append(buffer)
                    buffer = ""
                cleaned_lines.append("")
                continue

            # Simple heuristic: if a line ends with a hyphen, it's likely a broken word.
            if buffer.endswith('-'):
                buffer = buffer[:-1] + line
            # Simple heuristic: if a line starts with a lowercase letter, it's likely a continuation.
            elif buffer and line and line[0].islower():
                buffer += " " + line
            # If the line looks like a heading or new paragraph, push the buffer.
            elif len(line) > 1 and (line[0].isupper() and (not buffer or buffer.endswith('.'))):
                if buffer:
                    cleaned_lines.append(buffer)
                buffer = line
            else:
                if buffer:
                    buffer += " " + line
                else:
                    buffer = line
        
        if buffer:
            cleaned_lines.append(buffer)

        # Post-processing to fix common issues
        final_text = "\n".join(cleaned_lines)
        final_text = re.sub(r'\s+([.,!?])', r'\1', final_text) # Remove space before punctuation
        final_text = re.sub(r'—\s*', '—', final_text) # Clean up em dashes
        final_text = re.sub(r'\s*—', '—', final_text)
        final_text = re.sub(r'(\w)\s*-\s*(\w)', r'\1\2', final_text) # Rejoin hyphenated words split by spaces
        final_text = re.sub(r'\s{2,}', ' ', final_text) # Collapse multiple spaces into one

        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(final_text)

        print(f"Successfully cleaned '{input_file_path}' and saved to '{output_file_path}'")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    input_file = r"C:\dnd\books\Dungeon Master's Guide 2024.txt"
    output_file = r"C:\dnd\books\Dungeon Master's Guide 2024_cleaned.txt"
    clean_dnd_text(input_file, output_file)