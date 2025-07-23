import os
import re

def clean_md(_path):
    """Clean generated markdown files."""
    # TO DO  - properly lint, health check and clean files
    for folder, _, files in os.walk(_path):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(folder, file)
                print(f"Processing {file_path}")

                with open(file_path, 'r') as file:
                    content = file.read()
                
                # Strip trailing whitespace and - from the end of the file
                stripped_content = re.sub(r'([\s\n]*[-_]{4,}[\s\n]*)', '\n\n---\n\n', content)
                stripped_content = re.sub(r'([\s\n]*-{3,}[\s\n]*){2,}', '\n\n---\n\n', stripped_content)
                stripped_content = re.sub(r'[-\s\r\n]+$', '', stripped_content)
                with open(file_path, 'w') as file:
                    file.write(f"{stripped_content}\n")