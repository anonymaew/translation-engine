import { curryTop } from './curry';
import { webName } from './kube';
import { chatTask } from './ollama';

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

const translateText = curryTop(
  (pod: PodOptions, llm: LLMOptions) => async (texts: string[]) => {
    const translated = await chatTask(pod, llm, texts);
    return translated;
  }
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
    return Promise.reject(res.statusText);
  }

  const json = await res.json();
  const nouns = json.list
    .map(n => n.trim());
  return nouns;
}

const bulletsToList = (text: string) =>
  text
    .split('\n')
    .filter(n => n.trim()[0] === '-')
    .map(n => n.trim().slice(2));
const dontLostItems = (text1: string, text2: string) =>
  bulletsToList(text1).length === bulletsToList(text2).length;

const translateNouns = async (pod: PodOptions, options: LLMOptions, nouns: string[]) => {
  console.log(`Translating entities...`);
  const clumps = nouns
    .reduce((acc, n) => {
      if (acc.length === 0 || acc[acc.length - 1].length + n.length > 32)
        return [...acc, [n]];
      return [...acc.slice(0, -1), [...acc[acc.length - 1], n]];
    }, [])
    .map(clump => clump.map(n => `- ${n}`).join('\n'));

  const llm = { ...options, validate: dontLostItems };
  const translated = await chatTask(pod, llm, clumps);
  return translated
    .map(t =>
      t.split('\n')
        .filter(n => n.trim()[0] === '-')
        .map(n => n.trim().slice(2)))
    .flat();
}

const replaceNouns = (translatePod: PodOptions, entityPod: PodOptions, translateEntityOptions: LLMOptions, src: string) => async (texts: string[]) => {  
  const text = texts.join('\n');
  const entityServer = `https://${webName(1, entityPod)}`;
  const nouns = await extractNouns(entityServer, text, src);
  const translatedNouns = await translateNouns(translatePod, translateEntityOptions, nouns);
  const nounDict = nouns
    .map((n, i) => ({ noun: n, translated: translatedNouns[i] }));
  const replaced = texts
    .map(t => nounDict
      .reduce((acc, n) => acc.replace(n.noun, n.translated), t));
  return replaced;
}

const replaceTranslateNouns = curryTop(replaceNouns);

const rewriteText = curryTop(
  (pod: PodOptions, llm: LLMOptions) => async (texts: string[]) => {
    const rewrites = await chatTask(pod, llm, texts);
    return rewrites;
  }
);

export {
  replaceTranslateNouns,
  translateText,
  rewriteText,
};
