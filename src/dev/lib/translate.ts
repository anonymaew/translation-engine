import { $ } from 'bun';
import { curryWrap } from './curry';
import { webName } from './kube';

const model_check = async (server, model) => {
  const res = await fetch(`${server}/api/tags`);
  const json = await res.json();
  const exists = json.models.some(m => m.name === model);
  if (!exists) {
    console.log(`model ${model} not found, pulling...`);
    const response = await fetch(
      `${server}/api/pull`,
      {
        method: 'POST',
        body: JSON.stringify({
          name: model,
        }),
      }
    );
    const ok = await response.text();
  }
};

enum TranslateMode {
  Non = 'no context',
  Seq = 'sequential',
  Sec = 'sequential with context window',
}

type TranslateOptions = {
  model: string,
  options: any,
  prompt?: string,
  src: string,
  tar: string,
  mode: TranslateMode,
};

const isNothing = (text: string) => text === '' || text === '\n' || text === '\n\n';

const translateJob = async (server, messages, options) => {
  await model_check(server, options.model);

  const controller = new AbortController();
  const signal = controller.signal;

  const res = await Promise.race([
    fetch(
      `${server}/api/chat`,
      {
        signal,
        method: 'POST',
        body: JSON.stringify({
          messages,
          options: options.options,
          model: options.model,
          stream: false,
        }),
      }
    ),
    // timeout in case of model hangs up
    new Promise((resolve, _) => setTimeout(() => resolve({
      ok: false,
      statusText: `timeout on ${server}`,
    }), 1000 * 45))
  ]);

  // tell the model to abort if timeout, otherwise we lose control
  if (!res.ok) {
    controller.abort();
    return Promise.reject(res.statusText);
  }

  const json = await res.json();
  const para = json.message.content.trim();

  return para;
};

const translate = (options: TranslateOptions, pod: PodOptions) => async (texts: string[]) => {
  const result = [];
  const window = 10;
  const system = `Ignore the ${options.tar} text. Please translate a given ${options.src} sentence into ${options.tar}. Please do not add more notes or explanations.`;
  const server = `https://${webName(1, pod)}`;

  for (const text of texts) {
    if (isNothing(text))
      continue;
    const prev = (options.mode === TranslateMode.Sec)
      ? result.slice(-2 * window)
      : [];
    const messages = [
      { role: 'system', content: options.prompt || system },
      ...prev,
      { role: 'user', content: text },
    ];
    const translated = await translateJob(server, messages, options);
    result.push({ role: 'user', content: text });
    result.push({ role: 'assistant', content: translated });
    console.log(result.slice(-2 * window));
  }
  return result
    .filter(m => m.role === 'assistant')
    .map(m => m.content);
};

const translateText = curryWrap(
  translate,
  () => async (text: string[]) => text
);

const extractNouns = async (server: string, text: string, lang: string) => {
  if (nounSupportedLangs.map(l => l.lang).indexOf(lang) === -1) {
    console.log(`Language ${lang} not supported, skip entity extraction.`);
    return [];
  }

  console.log(`Extracting ${lang} entities...`);
  const res = await fetch(
    server,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text,
        lang: nounSupportedLangs.find(l => l.lang === lang).model,
      }),
    }
  );
  if (!res.ok) {
    console.log('response not ok');
    return Promise.reject(res.statusText);
  }

  const json = await res.json();
  const nouns = json.list
    .map(n => n.trim());
  return nouns;
}

const translateNouns = async (nouns: string[], options: TranslateOptions, pod: PodOptions) => {
  const nounDict = nouns
    .map(n => ({ noun: n, translated: '' }));
  const completed = [];

  while (nounDict.length > 0) {
    const clump_n = 32;
    const selected = nounDict
      .splice(0, clump_n);
    const clump = selected
      .map(n => `- ${n.noun}`)
      .join('\n');
    const translated = await translate(options, pod)([clump]);
    const translatedNouns = translated[0]
      .split('\n')
      .filter(n => n.trim()[0] === '-')
      .map(n => n.trim().slice(2))
      .map((n, i) => ({ ...selected[i], translated: n }));
    if (translatedNouns.length === selected.length) {
      completed.push(...translatedNouns);
      translatedNouns.forEach(n => console.log(`${n.noun} -> ${n.translated}`));
      console.log(`Entity translated: ${completed.length}/${nouns.length}`);
    }
    else {
      console.log(`Translated entities are not correct, retrying...`);
      nounDict.push(...(selected.sort((a, b) => Math.random() - 0.5)));
    }
  }

  return completed;
}

const replaceNouns = (src: string, tar: string, translatePod: PodOptions, entityPod: PodOptions) => async (texts: string[]) => {  
  const text = texts.join('\n');
  const entityServer = `https://${webName(1, entityPod)}`;
  const translateOptions = {
    model: 'mistral:latest',
    prompt: `Translate the following list of ${src} entities into short ${tar}.`,
    options: {
      temperature: 0.4,
    },
    src,
    tar,
    mode: TranslateMode.Seq,
  };
  const nouns = await extractNouns(entityServer, text, src);
  const translatedNouns = await translateNouns(nouns, translateOptions, translatePod);
  const replaced = texts
    .map(t => translatedNouns
      .reduce((acc, n) => acc.replace(n.noun, n.translated), t));
  return replaced;
}

const replaceTranslateNouns = curryWrap(
  replaceNouns,
  () => async (texts: string[]) => texts
);

export {
  replaceTranslateNouns,
  translateText,
  TranslateMode,
};

const nounSupportedLangs = [
  { lang: 'Catalan', code: 'ca', model: 'ca_core_news_sm' },
  { lang: 'Chinese', code: 'zh', model: 'zh_core_web_sm' },
  { lang: 'Croatian', code: 'hr', model: 'hr_core_news_sm' },
  { lang: 'Danish', code: 'da', model: 'da_core_news_sm' },
  { lang: 'Dutch', code: 'nl', model: 'nl_core_news_sm' },
  { lang: 'English', code: 'en', model: 'en_core_web_sm' },
  { lang: 'Finnish', code: 'fi', model: 'fi_core_news_sm' },
  { lang: 'French', code: 'fr', model: 'fr_core_news_sm' },
  { lang: 'German', code: 'de', model: 'de_core_news_sm' },
  { lang: 'Greek', code: 'el', model: 'el_core_news_sm' },
  { lang: 'Italian', code: 'it', model: 'it_core_news_sm' },
  { lang: 'Japanese', code: 'ja', model: 'ja_core_news_sm' },
  { lang: 'Korean', code: 'ko', model: 'ko_core_news_sm' },
  { lang: 'Lithuanian', code: 'lt', model: 'lt_core_news_sm' },
  { lang: 'Macedonian', code: 'mk', model: 'mk_core_news_sm' },
  { lang: 'Norwegian Bokmål', code: 'nb', model: 'nb_core_news_sm' },
  { lang: 'Polish', code: 'pl', model: 'pl_core_news_sm' },
  { lang: 'Portuguese', code: 'pt', model: 'pt_core_news_sm' },
  { lang: 'Romanian', code: 'ro', model: 'ro_core_news_sm' },
  { lang: 'Russian', code: 'ru', model: 'ru_core_news_sm' },
  { lang: 'Slovenian', code: 'sl', model: 'sl_core_news_sm' },
  { lang: 'Spanish', code: 'es', model: 'es_core_news_sm' },
  { lang: 'Swedish', code: 'sv', model: 'sv_core_news_sm' },
  { lang: 'Ukrainian', code: 'uk', model: 'uk_core_news_sm' },
];
