# The main file for the program
# Author: Korben Tompkin

# The following program is middleware for a translation engine
# Powered by Large Language Models installed with ollama
# The engine accepts Chinese text and translates it to Academic English
# The engine runs inside of a docker container

# The model API is exposed on port 11434

# The following program accepts a string of Chinese text
# It then translates the text to English by making a request to the model API
# The program then returns the English translation

import sys
import os
import time
from docx import Document
from lib.translation import translate

# The exposed port for the model API
PORT = 11434

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
    translation = translate(path, PORT)

    # Stop the timer
    end = time.time()
