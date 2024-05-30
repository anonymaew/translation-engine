# from lib.translate import replace_translate_nouns
from lib.chatagent import OllamaAgent, OpenAIAgent
from lib.doctext import Document
from lib.translate import EntityAgent

# filename = 'Dynastic Histories and Kinship Business-Introduction.docx'
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
    'model': 'thinkverse/towerinstruct',
    'options': {
        'temperature': 0.8,
        'num_ctx': 9999,
    },
    # 'prompt': f'Romanize the following list of {src} entities into {tar}, present in dash bullet points and do not include the original {src} language.',
    # 'prompt': f'Ignore the {tar} text. Please translate the given {src} entity into {tar}, only give one concise translation result.',
    'user_prompt': lambda text, paragraph: f"Translate the entity from {src} to {tar}\n\n{src} entity: {text}\n\n{tar}: ",
}
extract_entity_options = {
    'src': src,
    'label': ['PERSON', 'GPE', 'LOC', 'ORG', 'FAC', 'EVENT', 'NORP', 'WORK_OF_ART', 'PRODUCT'],
    # 'label': ['PERSON', 'LOC', 'WORK_OF_ART'],
}
translate_main_options = {
    'model': 'thinkverse/towerinstruct',
    'options': {
        'temperature': 0,
        'num_ctx': 9999,
    },
    # 'prompt': f'Ignore the {tar} text. Please translate the {src} language sentence into {tar} language using the vocabulary and expressions of the native speaker of the {tar} language. Please translate the footnotes and retain their original format. Please use a concise, clear, and formal tone of voice and academic writing style. Please do not give any alternative translation or including any notes or discussion.',
    'user_prompt': lambda text: f'Translate the following markdown text from {src} to {tar}. \n\n{src}: {text}\n\n{tar}:',
    # 'context': 2,
    # 'prime': [
    #     '戴震天算学中国化的意义',
    #     'The Significance of Dai Zhen\'s Mathematics Localization in China',
    # ],
}


if __name__ == '__main__':
    agent = OllamaAgent(translate_pod)
    # agent = OpenAIAgent()
    entity = EntityAgent(agent, entity_pod, extract_entity_options)
    file = Document(filename)
    file.md = entity.task(str(file), translate_entity_options)
    jobs = file.split('paragraphs')
    translated = agent.task(jobs, translate_main_options)
    file.export(translated)
