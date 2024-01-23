import { JobManager } from './sem';

const regex_footnotemark = /\[\^(\d+)\][^:]/g;
const regex_footnote = /\[\^(\d+)\]:\s*(.*)/g;

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

// for checking if translated text still keeps all footnotes intact or not
const footnote_check = (result_text, original) => {

  const footnote_list = [...original.matchAll(regex_footnote)]
    .map(m => m[1]);
  const footnotemarks = [...result_text.matchAll(regex_footnotemark)]
    .map(m => m[1]);
  const footnotes = [...result_text.matchAll(regex_footnote)]
    .map(m => m[1]);

  // compare footnote marks and bottom footnote by equality and by order.
  if (JSON.stringify(footnotemarks) === JSON.stringify(footnote_list) &&
      JSON.stringify(footnotes) === JSON.stringify(footnote_list))
    return { match: true };
  else
    return {
      match: false,
      // for debugging
      detail: {
        expected: footnote_list,
        result: [footnotemarks, footnotes],
      }
    };
};

const translate = async (server, text, model) => {
  await model_check(server, model);

  // for prompting (somehow works better with explicitly telling what are those footnote marks)
  const footnote = [...text.matchAll(regex_footnotemark)]
    .map(m => m[1])
    .map(m => `[^${m}]`).join(',');

  const system = `You are a translator. Your job is to translate a given chinese text into english, word by word, without adding notes or explanations. Keep the markdown format as is.${footnote.length == 0 ? '' : ` You must leave footnote marks (${footnote}) where they were and keep them in the translated text.`}`;
  const prompt = text;

  const controller = new AbortController();
  const signal = controller.signal;

  const res = await Promise.race([
    fetch(
      `${server}/api/generate`,
      {
        signal,
        method: 'POST',
        body: JSON.stringify({
          model,
          stream: false,
          system,
          prompt,
          options: {
            temperature: 0.2,
          }
        }),
      }
    ),
    // timeout in case of model hangs up
    new Promise((resolve, _) => setTimeout(() => resolve({
      ok: false,
      statusText: 'timeout',
    }), 1000 * 45))
  ]);

  // tell the model to abort if timeout, otherwise we lose control
  if (!res.ok) {
    controller.abort();
    return Promise.reject(res.statusText);
  }

  const json = await res.json();
  const para = json.response.trim();

  // check if footnote matches
  const check_footnote = footnote_check(para, text);
  if (!check_footnote.match)
    return Promise.reject(`footnote mismatch: ${JSON.stringify(check_footnote.detail)}`);

  // console.log(`${model} (${text.length} chars) translated successfully ------------\n${para}`);
  return para;
};

// grouping paragraph with its footnotes for better context
const group_footnotes = (paragraphs) => {
  const paragraph_label = paragraphs
    .filter(p => !p.match(regex_footnote))
    .map((p, i) => {
      const marks = [...p.matchAll(regex_footnotemark)].map(m => m[1]);
      return {
        paragraph: p,
        marks,
      };
  });

  const fullText = paragraphs.join('\n\n');
  const footnotes = [...fullText.matchAll(regex_footnote)];

  const grouped = paragraph_label.map(p => {
    const footnote = p.marks
      .map(m => footnotes.find(f => f[1] === m)[0])
      .join('\n\n');
    return p.paragraph + '\n\n' + footnote;
  });
  return grouped;
};

// grouping footnotes individually (paragraph/sentence)
const group_text_footnotes = (text) => {
  const footnotes = [...text.matchAll(regex_footnote)];
  const paragraphs = text
    .split('\n\n')
    .filter(p => !p.match(regex_footnote))
    .map((p, i) => {
      return p
        .split(/(?<=\[\^\d+\])/)
        .map(s => {
          const mark = [...((s+' ').matchAll(regex_footnotemark))];
          if (mark.length === 0)
            return {
              paragraph: s,
              paragraph_index: i,
            };
          const footnote = footnotes
            .find(f => f[1] === mark[0][1]);
          return {
            paragraph: `${s}\n\n${footnote[0]}`,
            paragraph_index: i,
          };
        });
    })
    .flat();
  return paragraphs;
};

const regroup_text_footnotes = (paragraphs) => {
  return paragraphs
    .reduce((acc, p) => {
      if (acc.length === 0)
        return [[p.paragraph]];
      if (p.paragraph_index === acc.length - 1)
        return [...acc.slice(0, -1), [...acc[acc.length - 1], p.paragraph]];
      return [...acc, [p.paragraph]];
    }, [])
    .map(p => {
      const org_p = p
        .map(s => {
          const footnotes = [...s.matchAll(regex_footnote)]
            .map(m => m[0])
          const sentence = s
            .split('\n\n')
            .filter(s => !s.match(regex_footnote))
            .join('');
          return {sentence, footnotes};
          // if (footnotes.length === 0)
          //   return `${sentence}\n\n`;
          // return `${sentence}\n\n${footnotes}\n\n`;
        })
        .reduce((acc, s) => { 
          return {
            sentence: acc.sentence + s.sentence,
            footnotes: [...acc.footnotes, ...s.footnotes],
          };
        }, {sentence: '', footnotes: []});
      if (org_p.footnotes.length === 0)
        return org_p.sentence;
      return `${org_p.sentence}\n\n${org_p.footnotes.join('\n\n')}`;
    })
    .join('\n\n');
}

// grouping paragraphs to a bigger paragraph. model seems to perform better with larger text
const group_clumps = (paragraphs, chars) => {
  return paragraphs.reduce((acc, p) => {
    if (acc.length === 0)
      return [p];

    const last = acc[acc.length - 1];
    if (last.length + p.length < chars)
      return [...acc.slice(0, -1), last + '\n\n' + p];
    else
      return [...acc, p];
  }, []);
};

// the real task, translate a file with a model
const task = async (filename, model) => {
  const file = Bun.file(`${filename}.md`);
  const text = await file.text();
  const paragraphs = text.split('\n\n').map(p => p.trim());
  // const grouped = group_clumps(group_footnotes(paragraphs), 1000);
  const grouped = group_text_footnotes(text);

  const num_workers = 1;
  const workers = Array(num_workers)
    .fill(0)
    .map((_,i) =>
      async(job) => {
        const paragraph = await translate(`https://${i+1}-dcct.nrp-nautilus.io` , job.p.paragraph, job.model);
        return {
        paragraph,
        paragraph_index: job.p.paragraph_index,
      }}
    );
  const jobs = grouped
    .map(p => ({ p, model }));
  const manager = new JobManager(workers, {
      verbose: true,
      cache: true,
    });
  const translated = await manager.run(jobs);

  const data = regroup_text_footnotes(translated);
  await Bun.write(`${filename}-translated-${model}.md`, data);
};

const models:string[] = [
  // 'llama2',
  'mistral:latest',
  // 'llama2-uncensored',
  // 'mixtral',
]

// const file = Bun.file(`chinese.md`);
// const text = await file.text();
// const paragraphs = group_text_footnotes(text);
// const regrouped = regroup_text_footnotes(paragraphs);
// console.log(regrouped);
// await Bun.write(`chinese-regrouped.md`, regrouped);

for (const model of models) {
  await task('chinese', model);
}
