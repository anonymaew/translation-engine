# from lib.translate import replace_translate_nouns
from lib.chatagent import OllamaAgent, OpenAIAgent
from lib.doctext import Document
from lib.translate import EntityAgent

filename = '戴震天算学中国化的意义.docx'
src = 'Chinese'
tar = 'English'

translate_pod = {
    'name': 'translate',
    'image': 'ollama/ollama:0.1.34',
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
    'model': 'gemma:latest',
    'options': {
        'temperature': 0.2,
        'num_ctx': 9999,
    },
    # 'prompt': f'Romanize the following list of {src} entities into {tar}, present in dash bullet points and do not include the original {src} language.',
    'prompt': f'Romanize the given {src} entity into {tar}, only give one translation result.',
    'prime': [
        '史册',
        'Historical records',
        '编年史',
        'Chronicles',
        '考古',
        'Archaeology',
    ],
}
extract_entity_options = {
    'src': src,
    'label': ['PERSON', 'GPE', 'LOC', 'ORG', 'FAC', 'EVENT', 'NORP', 'WORK_OF_ART', 'PRODUCT'],
    # 'label': ['PERSON', 'LOC', 'WORK_OF_ART'],
}
translate_main_options = {
    'model': 'llama3:latest',
    'options': {
        'temperature': 0,
        'num_ctx': 9999,
    },
    'prompt': f'Ignore the {tar} text. Please translate the {src} language sentence into {tar} language using the vocabulary and expressions of the native speaker of the {tar} language and include the footnotes. Retain the original format and footnotes. Do not self-reference. You are an expert translator tasked with improving a text\'s spelling, grammatical, and literary quality. Please use a concise, clear, and formal tone of voice and academic writing style. Please do not give any alternative translation or including any notes or discussion.',
    'context': 2,
    # 'prime': [
    #     '戴震天算学中国化的意义',
    #     'The Significance of Dai Zhen\'s Mathematics Localization in China',
    # ],
}

rewrite_options = {
    'model': 'mistral:latest',
    'options': {
        'temperature': 0,
        'num_ctx': 9999,
    },
    'prompt': f'Rewrite the following sentence into formal and academic {tar}. do not include any additional discussion or comment.',
}

if __name__ == '__main__':
    agent = OllamaAgent(translate_pod)
    # agent = OpenAIAgent()
    entity = EntityAgent(agent, entity_pod, extract_entity_options)
    file = Document(filename)
    file.md = entity.task(str(file), translate_entity_options)
    jobs = file.split('sentences')
    translated = agent.task(jobs, translate_main_options)
    file.export(translated)
