from .chatagent import ChatAgent
from .kube import Pod
import more_itertools
import requests
from time import sleep


noun_supported_langs = [
    {'lang': 'Catalan', 'code': 'ca', 'model': 'ca_core_news_sm'},
    {'lang': 'Chinese', 'code': 'zh', 'model': 'zh_core_web_trf'},
    {'lang': 'Croatian', 'code': 'hr', 'model': 'hr_core_news_sm'},
    {'lang': 'Danish', 'code': 'da', 'model': 'da_core_news_sm'},
    {'lang': 'Dutch', 'code': 'nl', 'model': 'nl_core_news_sm'},
    {'lang': 'English', 'code': 'en', 'model': 'en_core_web_trf'},
    {'lang': 'Finnish', 'code': 'fi', 'model': 'fi_core_news_sm'},
    {'lang': 'French', 'code': 'fr', 'model': 'fr_core_news_sm'},
    {'lang': 'German', 'code': 'de', 'model': 'de_core_news_sm'},
    {'lang': 'Greek', 'code': 'el', 'model': 'el_core_news_sm'},
    {'lang': 'Italian', 'code': 'it', 'model': 'it_core_news_sm'},
    {'lang': 'Japanese', 'code': 'ja', 'model': 'ja_core_news_sm'},
    {'lang': 'Korean', 'code': 'ko', 'model': 'ko_core_news_sm'},
    {'lang': 'Lithuanian', 'code': 'lt', 'model': 'lt_core_news_sm'},
    {'lang': 'Macedonian', 'code': 'mk', 'model': 'mk_core_news_sm'},
    {'lang': 'Norwegian Bokmål', 'code': 'nb', 'model': 'nb_core_news_sm'},
    {'lang': 'Polish', 'code': 'pl', 'model': 'pl_core_news_sm'},
    {'lang': 'Portuguese', 'code': 'pt', 'model': 'pt_core_news_sm'},
    {'lang': 'Romanian', 'code': 'ro', 'model': 'ro_core_news_sm'},
    {'lang': 'Russian', 'code': 'ru', 'model': 'ru_core_news_sm'},
    {'lang': 'Slovenian', 'code': 'sl', 'model': 'sl_core_news_sm'},
    {'lang': 'Spanish', 'code': 'es', 'model': 'es_core_news_sm'},
    {'lang': 'Swedish', 'code': 'sv', 'model': 'sv_core_news_sm'},
    {'lang': 'Ukrainian', 'code': 'uk', 'model': 'uk_core_news_sm'},
]


def bullets_to_list(text):
    lines = text.split('\n')
    bullet_lines = filter(lambda x: x.strip()[:1] == '-', lines)
    points = list(map(lambda x: x.strip()[2:], bullet_lines))
    return points


def dont_lost_items(text1, text2):
    # return len(bullets_to_list(text1)) == len(bullets_to_list(text2))
    return len(text2.split('\n')) == len(text1.split('\n'))


def first_paragraph_with_word(paragraphs, word):
    for p in paragraphs:
        if word in p:
            return p
    return None


def translate_nouns(translate_pod, translate_entity_options, nouns, text):
    print('Translating entities...')
    clumps = more_itertools.chunked(nouns, 1)
    paragraphs = text.split('\n\n')
    clumps_str = list(map(lambda c: '\n'.join(
        # list(map(lambda w: f'- {w}', c))), clumps))
        list(map(lambda w: f'{translate_entity_options['user_prompt'](w, first_paragraph_with_word(paragraphs, w)) if 'user_prompt' in translate_entity_options else w}', c))), clumps))

    # delete user_prompt
    translate_entity_options.pop('user_prompt', None)
    translated_chunks = translate_pod.task(
        clumps_str, translate_entity_options)
    translated = ('\n'.join(translated_chunks)).split('\n')
    translated_words = list(map(lambda x: x.strip()[2:], translated))
    return translated_words


class EntityAgent():
    def __init__(self,
                 translate_pod,
                 entity_pod,
                 extract_entity_options):
        self.translate_pod = translate_pod
        self.entity_pod = Pod(entity_pod)
        self.extract_entity_options = extract_entity_options
        self.start()
        self.server = None

    def start(self):
        self.entity_pod.up()

    def prepare(self):
        self.entity_pod.port_forward(5000)
        self.server = 'http://localhost:5000'
        sleep(3)

    def error_handler(self, e):
        err_str = str(e)
        if 'supported' in err_str:
            print(err_str)
        else:
            raise e

    def task(self, text, llm):
        try:
            self.prepare()
            options = self.extract_entity_options
            the_lang = [lang for lang in noun_supported_langs if lang['lang']
                        == options['src']] or None
            if the_lang is None:
                raise Exception(
                    f'{options["src"]} not supported, skip entity extraction')

            print(f'Extracting {options["src"]} entities...')
            res = requests.post(
                f'{self.server}',
                json={
                    'text': text,
                    'lang': the_lang[0]['model'],
                    'label': self.extract_entity_options['label']
                },
            )

            json = res.json()
            nouns = list(map(lambda x: x.strip(), json['list']))
            translated_nouns = translate_nouns(
                self.translate_pod, llm, nouns, text)
            noun_dict = dict(zip(nouns, translated_nouns))
            for k, v in noun_dict.items():
                text = text.replace(k, v)
            return text

        except Exception as e:
            self.error_handler(e)
            return text
