#!/usr/bin/env python3

from flask import Flask, request, jsonify
import spacy
import time
import subprocess
import os

app = Flask(__name__)
models_path = os.environ.get("MODELS_PATH", "/models")


@app.route('/install', methods=['POST'])
def install():
    lang = request.get_json()['lang']
    subprocess.Popen(f'find {models_path} | grep {lang} | xargs -I{{}} pip install {{}}',
                     shell=True)
    return jsonify({'status': 'done'})


@app.route('/', methods=['POST'])
def extract():
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
