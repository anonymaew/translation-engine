import { useKubernetes } from './lib/kube';
import { curryCompose } from './lib/curry';
import {
  replaceTranslateNouns,
  translateText,
  TranslateMode
} from './lib/translate';
import {
  fileToMDString,
  splitByParagraphs,
  splitBySentences,
  removeFootnotes,
  clumpText
} from './lib/doctext';

const filename = 'chinese.docx';
const src = 'Chinese';
const tar = 'English';
const translatePod = {
  num: 1,
  name: 'translate',
  image: 'ollama/ollama:0.1.22',
  port: 11434,
  gpu: 'NVIDIA-A10',
  command: ['/bin/sh', '-c', 'nvidia-smi && ollama serve'],
  standby: true,
};
const entityPod = {
  num: 1,
  name: 'entity',
  image: 'nsrichan/ai4humanities-translation-engine:entities',
  port: 5000,
  gpu: 'NVIDIA-A10',
  standby: true,
};
const translateOptions = {
  model: 'mistral:latest',
  options: {
    temperature: 0, 
    num_ctx: 4096,
  },
  prompt: `Ignore the ${tar} text. Please translate a given ${src} sentence into short ${tar}, focusing on preserving the content, tone, and sentiment. Do not include any discussion, provide only the translated text`,
  mode: TranslateMode.Seq
};

const pipeline = curryCompose(
  useKubernetes(translatePod),
  useKubernetes(entityPod),
  fileToMDString(filename),
  removeFootnotes(),
  splitBySentences(),
  replaceTranslateNouns(src, tar, translatePod, entityPod),
  translateText(translateOptions, translatePod),
) 

await pipeline();
