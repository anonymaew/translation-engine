import { useKubernetes } from './lib/kube';
import { curryCompose } from './lib/curry';
import {
  replaceTranslateNouns,
  translateText,
  rewriteText
} from './lib/translate';
import { ModeGenerate } from './lib/ollama';
import {
  fileToMDString,
  splitByParagraphs,
  splitBySentences,
  removeFootnotes,
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

const translateEntityOptions = {
  model: 'mistral:latest',
  options: {
    temperature: 0.4,
  },
  prompt: `Translate the following list of ${src} entities into short ${tar}.`,
  mode: ModeGenerate.Non,
};
const extractEntityOptions = {
  src,
  // label: ['PERSON', 'GPE', 'LOC', 'ORG', 'FAC', 'EVENT', 'NORP', 'WORK_OF_ART', 'PRODUCT'],
  label: ['PERSON', 'NORP', 'WORK_OF_ART'],
};
const translateMainOptions = {
  model: 'mistral:latest',
  options: {
    temperature: 0,
    // num_ctx: 4096,
  },
  prompt: `Ignore the ${tar} text. Please translate the given ${src} sentence into formal and academic ${tar} without any comment or discussion. Do not include any additional discussion or comment.`,
  mode: ModeGenerate.Non,
};
const rewriteOptions = {
  model: 'mistral:latest',
  options: {
    temperature: 0,
  },
  prompt: `Rewrite the following sentence into formal and academic ${tar}. do not include any additional discussion or comment.`,
  mode: ModeGenerate.Non,
}

const pipeline = curryCompose(
  useKubernetes({ options: translatePod }),
  useKubernetes({ options: entityPod }),
  fileToMDString({ filename }),
  removeFootnotes({}),
  splitBySentences({}),
  // splitByParagraphs({}),
  // replaceTranslateNouns({ translatePod, entityPod, translateEntityOptions, extractEntityOptions }),
  translateText({ pod: translatePod, llm: translateMainOptions }),
  rewriteText({ pod: translatePod, llm: rewriteOptions }),
)

await pipeline({});
