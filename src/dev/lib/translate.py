from .curry import curry_top
from .ollama import chat_task
from .kube import web_name, pod_obj
import requests
import more_itertools


noun_supported_langs = [
    {'lang': 'Catalan', 'code': 'ca', 'model': 'ca_core_news_sm'},
    {'lang': 'Chinese', 'code': 'zh', 'model': 'zh_core_web_sm'},
    {'lang': 'Croatian', 'code': 'hr', 'model': 'hr_core_news_sm'},
    {'lang': 'Danish', 'code': 'da', 'model': 'da_core_news_sm'},
    {'lang': 'Dutch', 'code': 'nl', 'model': 'nl_core_news_sm'},
    {'lang': 'English', 'code': 'en', 'model': 'en_core_web_sm'},
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


translate_text = curry_top(
    lambda config: lambda texts: chat_task(
        pod_obj(config[0]), config[1], texts)
)


def extract_nouns(server, text, options):
    the_lang = [lang for lang in noun_supported_langs if lang['lang']
                == options['src']] or None
    if the_lang is None:
        print(f'Language {
              options['src']} is not supported, skip entity extraction...')
        return []

    print(f'Extracting {options['src']} entities...')
    res = requests.post(
        f'{server}/api/extract',
        json={
            'text': text,
            'lang': the_lang[0]['model'],
            'label': options['label']
        },
    )

    json = res.json()
    res = list(map(lambda x: x.strip(), json['list']))
    return res


def bullets_to_list(text):
    lines = text.split('\n')
    bullet_lines = filter(lambda x: x.strip()[0] == '-', lines)
    points = list(map(lambda x: x.strip()[2:], bullet_lines))
    return points


def dont_lost_items(text1, text2):
    return bullets_to_list(text1).length() == bullets_to_list(text2).length()


def translate_nouns(translate_pod, translate_entity_options, nouns):
    print('Translating entities...')
    clumps = more_itertools.chunked(nouns, 32)
    clumps_str = list(map(lambda c: '\n'.join(
        list(map(lambda w: f'- {w}', c))), clumps))

    llm = translate_entity_options + {'validation': dont_lost_items}
    translated_chunks = chat_task(pod_obj(translate_pod), llm, clumps_str)
    translated = ('\n'.join(translated_chunks)).split('\n')
    translated_words = list(map(lambda x: x.strip()[2:], translated))
    return translated_words


def replace_nouns(config):
    def f(texts):
        translate_pod, entity_pod, translate_entity_options, extract_entity_options = config
        text = '\n'.join(texts)
        entity_server = f'https://{web_name(entity_pod)}'
        nouns = extract_nouns(entity_server, text, extract_entity_options)
        translted_nouns = translate_nouns(translate_pod,
                                          translate_entity_options,
                                          nouns)
        noun_dict = nouns.zip(translted_nouns)
        for k, v in noun_dict:
            text = text.replace(k, v)
        return text.split('\n')
    return f


replace_translate_nouns = curry_top(replace_nouns)
replace_translate_nouns = curry_top(replace_nouns)