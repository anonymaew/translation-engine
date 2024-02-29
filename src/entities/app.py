#!/usr/bin/env python3

from flask import Flask, request, jsonify
import spacy
import time

app = Flask(__name__)

@app.route('/', methods=['POST'])
def post():
    data = request.get_json()
    lang, text, label = data['lang'], data['text'], data['label']

    print(f"Extracting entities from {lang} model with {len(text)} chars")
    start = time.time()
    nlp = spacy.load(lang)
    doc = nlp(text)
    ents = list(set([ent.text for ent in doc.ents if ent.label_ in label]))
    duration = time.time() - start

    print(f"Got {len(ents)} entities (processed in {duration:.3f} s)")
    res = {'list': ents}
    return jsonify(res)
