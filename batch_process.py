import time
from docx import Document
import openai
import os
import re
from dotenv import load_dotenv

# Load the environment variables
load_dotenv('config.env')

# Set the API key from the .env file
API_KEY = os.getenv('API_KEY')
openai.api_key = API_KEY

# Function to handle rate limiting by waiting for 65 seconds
def handle_rate_limited_request(context_messages):
    while True:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=context_messages,
                temperature=0,
                max_tokens=256
            )
            return response
        except openai.error.RateLimitError:
            print("Rate limit reached, waiting for 65 seconds.")
            time.sleep(65)  # Wait for 65 seconds

# Function to segment a long text into smaller parts based on an approximate character limit
def segment_text(text, approx_max_chars=2000):
    # Regular expression to match sentence endings reliably
    sentence_endings = re.compile(r'(?<=[.!?]) +')
    sentences = sentence_endings.split(text)
    segments = []
    current_segment = ""

    for sentence in sentences:
        # Check if adding the next sentence would exceed the approximate max characters
        if len(current_segment) + len(sentence) <= approx_max_chars:
            current_segment += (sentence + " ") if current_segment else sentence
        else:
            # If the current segment is empty and the sentence is too long, split the sentence further
            if not current_segment:
                sub_sentences = re.findall('.{1,%d}(?:\\s+|$)' % approx_max_chars, sentence)
                segments.extend(sub_sentences)
            else:
                segments.append(current_segment)
                current_segment = sentence
    # Add the last segment if it contains any text
    if current_segment:
        segments.append(current_segment.strip())  # Strip the trailing space

    return segments

# Function to translate a piece of text using GPT-4, maintaining context
def translate_text(text, source_language, target_language, context_messages):
    # Segment text into manageable parts if it's too long
    text_segments = segment_text(text)
    full_translation = ""
    
    for segment in text_segments:
        # Append the user message to the context
        context_messages.append({"role": "user", "content": segment})
        
        # Perform the translation with the context
        response = handle_rate_limited_request(context_messages)
        
        # Extract the translation from the response
        translation = response.choices[0].message.content.strip()
        full_translation += translation + " "
        
        # Update the context with the model's reply
        context_messages.append({"role": "assistant", "content": translation})
        
        # Check and reduce the context if needed
        context_messages = context_messages[-10:]  # Keep only the last 10 messages

    # Remove the trailing space from the last segment
    full_translation = full_translation.strip()
    
    return full_translation, context_messages


# Function to translate an entire .docx document
def translate_docx(file_path, source_language, target_language, output_file_path):
    doc = Document(file_path)
    new_doc = Document()
    
    # Initial context setup for the translation task
    context_messages = [
        {
            "role": "system",
            "content": f"You will be provided with text in {source_language}, and your task is to translate it into {target_language}."
        }
    ]
    
    # Translate each paragraph in the document, maintaining context
    for i, paragraph in enumerate(doc.paragraphs[234:]):
        if paragraph.text.strip():  # Only translate non-empty paragraphs
            try:
                translation, context_messages = translate_text(
                    paragraph.text, source_language, target_language, context_messages
                )
                print(f"{translation} index: {i}")
                new_doc.add_paragraph(translation)
                # Save after every successful translation
                new_doc.save(output_file_path)
            except Exception as e:
                # If an error occurs, log it and save the current progress
                print(f"An error occurred: {e}")
                new_doc.save(output_file_path)
                raise

# Usage
source_language = "Chinese"
target_language = "English"
file_path = "国史家事.docx"  # Path to the input .docx file
output_file_path = "output.docx"  # Path to save the output .docx file

translate_docx(file_path, source_language, target_language, output_file_path)
