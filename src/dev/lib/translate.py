from .kube import port_forward
import more_itertools
import requests
from time import sleep
from tqdm import tqdm


noun_supported_langs = [
    {'lang': 'Catalan', 'code': 'ca', 'model': 'ca_core_news_trf'},
    {'lang': 'Chinese', 'code': 'zh', 'model': 'zh_core_web_trf'},
    {'lang': 'Croatian', 'code': 'hr', 'model': 'hr_core_news_lg'},
    {'lang': 'Danish', 'code': 'da', 'model': 'da_core_news_trf'},
    {'lang': 'Dutch', 'code': 'nl', 'model': 'nl_core_news_lg'},
    {'lang': 'English', 'code': 'en', 'model': 'en_core_web_trf'},
    {'lang': 'Finnish', 'code': 'fi', 'model': 'fi_core_news_lg'},
    {'lang': 'French', 'code': 'fr', 'model': 'fr_dep_news_trf'},
    {'lang': 'German', 'code': 'de', 'model': 'de_dep_news_trf'},
    {'lang': 'Greek', 'code': 'el', 'model': 'el_core_news_lg'},
    {'lang': 'Italian', 'code': 'it', 'model': 'it_core_news_lg'},
    {'lang': 'Japanese', 'code': 'ja', 'model': 'ja_core_news_trf'},
    {'lang': 'Korean', 'code': 'ko', 'model': 'ko_core_news_lg'},
    {'lang': 'Lithuanian', 'code': 'lt', 'model': 'lt_core_news_lg'},
    {'lang': 'Macedonian', 'code': 'mk', 'model': 'mk_core_news_lg'},
    {'lang': 'Norwegian Bokmål', 'code': 'nb', 'model': 'nb_core_news_lg'},
    {'lang': 'Polish', 'code': 'pl', 'model': 'pl_core_news_lg'},
    {'lang': 'Portuguese', 'code': 'pt', 'model': 'pt_core_news_lg'},
    {'lang': 'Romanian', 'code': 'ro', 'model': 'ro_core_news_lg'},
    {'lang': 'Russian', 'code': 'ru', 'model': 'ru_core_news_lg'},
    {'lang': 'Slovenian', 'code': 'sl', 'model': 'sl_core_news_trf'},
    {'lang': 'Spanish', 'code': 'es', 'model': 'es_dep_news_trf'},
    {'lang': 'Swedish', 'code': 'sv', 'model': 'sv_core_news_lg'},
    {'lang': 'Ukrainian', 'code': 'uk', 'model': 'uk_core_news_trf'},
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
    translated_words = list(map(lambda x: x.strip(), translated))
    return translated_words


class EntityAgent():
    def __init__(self,
                 translate_pod,
                 extract_entity_options):
        self.translate_pod = translate_pod
        self.extract_entity_options = extract_entity_options
        self.start()
        self.server = None

    def start(self):
        pass
        # self.entity_pod.up()

    def prepare(self):
        port_forward('entity', 5000)
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

            print(f'Preparing NER model ...')
            _res = requests.post(
                f'{self.server}/install',
                json={'lang': the_lang[0]['model']},
            )
            _res.json()

            print(f'Extracting {options["src"]} entities...')

            texts = text.split('\n\n')
            chunks = [texts[0]]
            for para in texts[1:]:
                if (len(chunks[-1]) > 2**10):
                    chunks += ['']
                chunks = chunks[:-1] + [chunks[-1] + '\n\n' + para]

            nouns = []
            for chunk in tqdm(chunks):
                res = requests.post(
                    f'{self.server}',
                    json={
                        'text': chunk,
                        'lang': the_lang[0]['model'],
                        'label': self.extract_entity_options['label']
                    },
                )
                json = res.json()
                nouns += list(map(lambda x: x.strip(), json['list']))

            translated_nouns = translate_nouns(
                self.translate_pod, llm, nouns, text)
            noun_dict = dict(zip(nouns, translated_nouns))
            for k, v in noun_dict.items():
                text = text.replace(k, v)
            return text

        except Exception as e:
            self.error_handler(e)
            return text
