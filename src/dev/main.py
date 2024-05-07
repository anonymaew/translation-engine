# from lib.translate import replace_translate_nouns
from lib.chatagent import OllamaAgent, OpenAIAgent
from lib.doctext import Document

filename = '戴震天算学中国化的意义.docx'
src = 'Chinese'
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
    'model': 'llama3:latest',
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
    'prompt': f'Ignore the {tar} text. Please translate the {src} language sentence into {tar} language using the vocabulary and expressions of the native speaker of the {tar} language. Refrain from explaning what you are doing. Do not self-reference. You are an expert translator tasked with improving a text\'s spelling, grammarical, literary quality. Please rewrite the translated text using a succinct, clear, and formal tone of voice and academic writing style from the perspective of a history professor. The text to be translated is a history book. Please do not give any alternative translation or including any comments or discussion.',
}
rewrite_options = {
    'model': 'mistral:latest',
    'options': {
        'temperature': 0,
    },
    'prompt': f'Rewrite the following sentence into formal and academic {tar}. do not include any additional discussion or comment.',
}

if __name__ == '__main__':
    agent = OllamaAgent(translate_pod, translate_main_options)
    # agent = OpenAIAgent(translate_main_options)
    file = Document(filename)
    jobs = file.split('sentences')
    translated = agent.task(jobs)
    file.export(translated)
