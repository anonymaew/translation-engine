import { $ } from 'bun';
import { JobManager } from './lib/sem';

// the real task, translate a file with a model
const task = async (filename, model) => {
  const file = Bun.file(`${filename}.md`);
  const text = await file.text();
  const paragraphs = new Paragraphs(text)
    .removeFootnotes()
    .clump(512);

  console.log(paragraphs.paragraphs.map(p => p.length));
  const num_workers = 4;
  const workers = Array(num_workers)
    .fill(0)
    .map((_,i) =>
      (job) => 
        translate(`https://${i+1}-dcct.nrp-nautilus.io` , job.p, job.model)
    );
  const jobs = paragraphs.paragraphs
    .map(p => ({ p, model }));
  const manager = new JobManager(workers, {
      verbose: true,
      cache: true,
    });
  const translated = await manager.run(jobs);

  // const data = regroup_text_footnotes(translated);
  const data = translated.join('\n\n');
  await Bun.write(`${filename}-translated-${model}.md`, data);
};

const models:string[] = [
  // 'llama2',
  'mistral:latest',
  // 'llama2-uncensored',
  // 'mixtral:latest',
]

// for (const model of models) {
//   await task('chinese', model);
// }

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

const filename = 'chinese.md';
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
  },
  src,
  tar,
  mode: TranslateMode.Seq
};

const pipeline = curryCompose(
  useKubernetes(translatePod),
  useKubernetes(entityPod),
  fileToMDString(filename),
  splitBySentences(),
  replaceTranslateNouns(src, tar, translatePod, entityPod),
  removeFootnotes(),
  translateText(translateOptions, translatePod),
) 

await pipeline();
