#!/usr/bin/env python3

from flask import Flask, request, jsonify
import spacy
import time

app = Flask(__name__)

@app.route('/', methods=['POST'])
def post():
    data = request.get_json()
    lang, text = data['lang'], data['text']

    start = time.time()
    nlp = spacy.load(lang)
    doc = nlp(text)
    ents = list(set([ent.text for ent in doc.ents if ent.label_ in ['PERSON', 'GPE', 'LOC', 'ORG', 'FAC', 'EVENT', 'NORP', 'WORK_OF_ART', 'PRODUCT']]))
    duration = time.time() - start

    print(f"Extracted by {lang} model with {len(text)} chars, got {len(ents)} entities (processed in {duration:.3f} s)")
    res = {'list': ents}
    return jsonify(res)
