#!/usr/bin/env python3

from flask import Flask, request, jsonify
import spacy
import time
import subprocess
import os

app = Flask(__name__)
models_path = os.environ.get("MODELS_PATH", "/models")
model = None


@app.route('/install', methods=['POST'])
def install():
    global model
    lang = request.get_json()['lang']
    subprocess.run(f'find {models_path} | grep {lang} | xargs -I{{}} pip install {{}}',
                   shell=True)
    model = spacy.load(lang)
    return jsonify({'status': 'done'})


@app.route('/', methods=['POST'])
def extract():
    global model
    data = request.get_json()
    lang, text, label = data['lang'], data['text'], data['label']

    print(f"Extracting entities from {lang} model with {len(text)} chars")
    start = time.time()
    doc = model(text)
    ents = list(set([ent.text for ent in doc.ents if ent.label_ in label]))
    duration = time.time() - start

    print(f"Got {len(ents)} entities (processed in {duration:.3f} s)")
    res = {'list': ents}
    return jsonify(res)
