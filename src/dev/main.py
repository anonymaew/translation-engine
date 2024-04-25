from lib.kube import use_kubernetes
from lib.curry import curry_compose
from lib.translate import replace_translate_nouns, translate_text
from lib.doctext import file_to_md_string, remove_footnotes, split_by_paragraphs

filename = 'Giustizia come vero apriori del tempo.docx'
src = 'Italian'
tar = 'English'

translate_pod = {
    'name': 'translate',
    'image': 'ollama/ollama:0.1.22',
    'gpu': 'NVIDIA-A10',
    'command': ['/bin/sh', '-c', 'nvidia-smi && ollama serve'],
    'standby': True,
}
entity_pod = {
    'name': 'entity',
    'image': 'nsrichan/ai4humanities-translation-engine:entities',
    'gpu': 'NVIDIA-A10',
    'standby': True,
}

translate_entity_options = {
    'model': 'mistral:latest',
    'options': {
        'temperature': 0.4,
    },
    'prompt': f'Translate the following list of {src} entities into short {tar}.',
}
extract_entity_options = {
    'src': src,
    # label: ['PERSON', 'GPE', 'LOC', 'ORG', 'FAC', 'EVENT', 'NORP', 'WORK_OF_ART', 'PRODUCT'],
    'label': ['PERSON', 'NORP', 'WORK_OF_ART'],
}
translate_main_options = {
    'model': 'llama3:latest',
    'options': {
        'temperature': 0,
        # num_ctx: 4096,
    },
    'prompt': f'Ignore the {tar} text. Please translate the given {src} sentence into formal and academic {tar} without any comment or discussion. Do not include any additional discussion or comment.',
}
rewrite_options = {
    'model': 'mistral:latest',
    'options': {
        'temperature': 0,
    },
    'prompt': f'Rewrite the following sentence into formal and academic {tar}. do not include any additional discussion or comment.',
}

pipeline = curry_compose([
    use_kubernetes(translate_pod),
    use_kubernetes(entity_pod),
    file_to_md_string(filename),
    remove_footnotes(None),
    split_by_paragraphs(None),
    replace_translate_nouns(
        translate_pod,
        entity_pod,
        translate_entity_options,
        extract_entity_options,
    ),
    translate_text(
        translate_pod,
        translate_main_options,
    ),
])

if __name__ == '__main__':
    pipeline(None)
