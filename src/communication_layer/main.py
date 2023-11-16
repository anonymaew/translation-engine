# The main file for the program
# Author: Korben Tompkin

# The following program is middleware for a translation engine
# Powered by Large Language Models installed with ollama
# The engine accepts Chinese text and translates it to Academic English
# The engine runs inside of a docker container
# The model API is exposed on port 11434

import sys
import os
import time
from lib.document import translate_docx, write_docx

if __name__ == "__main__":
    # The following code is executed when the program is run from the command line
    # Check if the user provided a file path
    if len(sys.argv) != 2:
        # Log the error
        print("Usage: python3 main.py <file>")
        # Exit the program
        sys.exit(1)

    # The path to the file
    path = sys.argv[1]

    # Check if the file exists
    if not os.path.exists(path):
        # Log the error
        print("File not found: " + path)
        # Exit the program
        sys.exit(1)

    # Check if the file is a Word document
    if not path.endswith(".docx"):
        # Log the error
        print("Invalid file type: " + path)
        # Exit the program
        sys.exit(1)

    # Start the timer
    start = time.time()

    # Translate the text now that the file has been validated
    translation = translate_docx(path)

    # Write the translated text to a new file
    write_docx(translation)

    # Stop the timer
    end = time.time()

    # Calculate the time elapsed
    elapsed = end - start

    # Log the time elapsed
    print(f"Translation completed in {elapsed} seconds")

    # Exit the program
    sys.exit(0)
