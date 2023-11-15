# Helper functions for working with .docx files
from docx import Document
from .translation import translate

# The following function accepts a .docx file
# It extracts the text from the file
# It splits the text into paragraphs
# It calls the translate function on each paragraph
# The function returns a list of English paragraphs
def translate_docx(docx):
    # The list of English paragraphs
    english = []

    # Extract the text from the file
    text = docx.paragraphs

    # Iterate through each paragraph
    for paragraph in text:
        # Translate the paragraph
        english.append(translate(paragraph.text))

    # Return the list of English paragraphs
    return english

# The following function accepts a .docx file
# It constructs a new .docx file with the translated text
# The function returns None
def write_docx(docx, english):
    # The document to be written
    document = Document()

    # Iterate through each paragraph
    for paragraph in english:
        # Write the paragraph to the document
        document.add_paragraph(paragraph)

    # Save the document
    document.save(docx)


