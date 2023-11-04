from docx import Document
import openai
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

load_dotenv('config.env')
API_KEY = os.getenv('API_KEY')

openai.api_key = API_KEY

def translate_text(text, source_language, target_language):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": f"You will be provided with a sentence in {source_language}, and your task is to translate it into {target_language}."
            },
            {
                "role": "user",
                "content": f"{text}"
            }
        ],
        temperature=0,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    translation = ''.join(response["choices"][0]["message"]["content"])
    return translation.strip()


def translate_paragraph(para, source_language, target_language):
    if para.text.strip():  
        return translate_text(para.text[:1], source_language, target_language)
    return None

def translate_docx(file_path, source_language, target_language, output_file_path):
    doc = Document(file_path)
    
    
    with ThreadPoolExecutor() as executor:

        results = list(executor.map(translate_paragraph, doc.paragraphs, [source_language]*len(doc.paragraphs), [target_language]*len(doc.paragraphs)))
    
    new_doc = Document()
    for translated_text in results:
        if translated_text is not None:
            new_doc.add_paragraph(translated_text)

    new_doc.save(output_file_path)

file_path = '国史家事.docx'
source_language = 'zh'
target_language = 'en'
output_file_path = 'Translated_国史家事.docx'

translate_docx(file_path, source_language, target_language, output_file_path)