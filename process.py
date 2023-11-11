import re
import time
import openai
from openai import OpenAI
from docx import Document
from dotenv import load_dotenv
import os

# Load the API key from an .env file
load_dotenv('config.env')
API_KEY = os.getenv('API_KEY')
client = OpenAI(api_key=API_KEY)

def split_into_paragraphs(file_path):
    doc = Document(file_path)
    return [(paragraph.text, paragraph.style) for paragraph in doc.paragraphs if paragraph.text.strip() != '']

def split_into_sentences(paragraph):
    return paragraph.split('. ')

def translate_text(sentences, source_language, target_language, client):
    context_messages = [{"role": "system", "content": f"Translate from {source_language} to {target_language}."}]
    for sentence in sentences[-4:]:  # Keep the context of the last 3 sentences plus the current one
        context_messages.append({"role": "user", "content": sentence})

    while True:
        try:
            response = client.chat.completions.create(model="gpt-4",
                                                      messages=context_messages,
                                                      temperature=0,
                                                      max_tokens=6969)
            return response.choices[0].message.content.strip()

        except openai.RateLimitError:
            time.sleep(65)
        except openai.OpenAIError as e:
            raise e

def create_translated_document(paragraphs, source_language, target_language, client, output_file_path):
    translated_doc = Document()
    curr = 0
    for paragraph, style in paragraphs:
        sentences = split_into_sentences(paragraph)
        translated_paragraph = []
        for i in range(len(sentences)):
            context_sentences = sentences[max(0, i-3):i+1] 
            translated_sentence = translate_text(context_sentences, source_language, target_language, client)
            translated_paragraph.append(translated_sentence.split('\n')[-1]) 
        print(f"{translated_paragraph} ix-> {curr}")
        curr += 1
        p = translated_doc.add_paragraph(' '.join(translated_paragraph))
        p.style = style
    translated_doc.save(output_file_path)


file_path = '国史家事.docx'
output_file_path = 'translated国史家事.docx'
source_language = 'zh'  
target_language = 'en'  

paragraphs = split_into_paragraphs(file_path)
create_translated_document(paragraphs, source_language, target_language, client, output_file_path)