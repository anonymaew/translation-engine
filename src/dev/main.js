const clean_junk = (text) => {
  return text
    .split('\n\n')
    .reverse()
    .reduce((acc, p) => {
      if (p.toLowerCase().includes('translat') && p[p.length - 1] === ':') {
        return acc;
      }
      return [p, ...acc];
    }, [])
    .join('\n\n');
};

const model_check = async (model) => {
  const res = await fetch('http://127.0.0.1:11434/api/tags');
  const json = await res.json();
  const exists = json.models.some(m => m.name === model);
  if (!exists) {
    const response = await fetch(
      'http://127.0.0.1:11434/api/pull',
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

const translate = async (text, model) => {
  const controller = new AbortController();
  const signal = controller.signal;
  const res = await Promise.race([
    fetch(
      'http://127.0.0.1:11434/api/generate',
      {
        signal,
        method: 'POST',
        body: JSON.stringify({
          model,
          stream: false,
          prompt: `Translate the following Chinese text into English:\n${text}\n\nEnglish translation:\n`,
          options: {
            temperature: 0,
          }
        }),
      }
    ),
    new Promise((resolve, reject) => setTimeout(() => resolve('timeout'), 1000 * 10)),
  ]);
  if (res === 'timeout') {
    console.error('timeout');
    controller.abort();
    return '';
  }
  console.log(res);
  // const ndjson = await res.text();
  const json = await res.json();
  const para = json.response.trim();
  // const para = ndjson
  //   .split('\n')
  //   .filter(l => l.length > 0)
  //   .map(l => JSON.parse(l).response)
  //   .join('')
  //   .trim();
  return para;
};

const job = async (filename, model) => {
  const file = Bun.file(`${filename}.md`);
  await model_check(model);

  const text = await file.text();
  const paragraphs = text.split('\n\n').map(p => p.trim());
  const translated = [];
  for (const p of paragraphs) {
    const t = await translate(p, model);
    console.log(`(${translated.length}) (${p.length} chars) (${model}) ------------`);
    console.log(t);
    translated.push(t);
  }

  const data = translated.join('\n\n');
  await Bun.write(`${filename}-translated-${model}.md`, data);
};

const models = [
  'llama2',
  'mistral',
  'llama2-uncensored',
  'mixtral',
]


const file = Bun.file(`chinese.md`);
const text = await file.text();
const paragraphs = text.split('\n\n').map(p => p.trim());
const res = await translate(paragraphs[181], 'llama2');
console.log(res)

for (const model of models) {
  await job('chinese', model);
}
