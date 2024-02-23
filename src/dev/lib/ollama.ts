import { webName, restartKubernetes } from './kube';

enum ModeGenerate {
  Par = 'parallel',
  Non = 'sequential with no context',
  Seq = 'sequential with context window',
}

type LLMOptions = {
  model: string,
  options: any,
  prompt: string,
  mode: ModeGenerate,
  window?: number,
  validation?: (org: string, res: string) => boolean,
};

const isNothing = (text: string) => text === '' || text === '\n' || text === '\n\n';

// checking whether the machine has the model
const model_check = async (server, model) => {
  // get all local models
  const res = await fetch(`${server}/api/tags`);
  const json = await res.json();
  const exists = json.models.some(m => m.name === model);
  // if not exists, pull the model via api
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

// handling single api request
const chatJob = async (server, llm, messages) => {
  await model_check(server, llm.model);

  // controller for timeout
  const controller = new AbortController();
  const signal = controller.signal;

  // fetching chat completion on Ollama api
  const res = await Promise.race([
    fetch(
      `${server}/api/chat`,
      {
        signal,
        method: 'POST',
        body: JSON.stringify({
          messages,
          options: llm.options,
          model: llm.model,
          stream: false,
        }),
      }
    ),
    // 45 sec timeout in case of model hangs up
    new Promise((resolve, _) => setTimeout(() => resolve({
      ok: false,
      statusText: `timeout on ${server}`,
    }), 1000 * 45))
  ]);

  // tell the model to abort if timeout, otherwise we lose control
  if (!res.ok) {
    controller.abort();
    return Promise.reject('LLM server just hung up, may need to restart the pod.');
  }

  const json = await res.json();
  const para = json.message.content.trim();

  return para;
};

// handling multiple texts (depends on mode)
const chatTask = async (pod: PodOptions, llm: LLMOptions, jobs: string[]) => {
  const pastResult = [];
  const result = [];
  const server = `https://${webName(1, pod)}`;

  for (let i = 0; i < jobs.length; i++) {
    const text = jobs[i];

    if (isNothing(text)) {
      result.push(text);
      continue;
    }
    const prev = (llm.mode === ModeGenerate.Seq)
      ? pastResult.slice(-2 * llm.window)
      : [];
    const messages = [
      { role: 'system', content: llm.prompt },
      ...prev,
      { role: 'user', content: text },
    ];
    const response = await chatJob(server, llm, messages)
      .catch(async (err) => {
        if (err !== 'LLM server just hung up, may need to restart the pod.')
          return Promise.reject(err);
        console.log(`LLM server hung up, restarting...`);
        await restartKubernetes(pod);
        i--;
        return '';
      });
    if (response === '')
      continue;

    if (llm.validation && !llm.validation(text, response)) {
      i--;
      continue;
    }

    if (llm.mode === ModeGenerate.Seq) {
      pastResult.push({ role: 'user', content: text });
      pastResult.push({ role: 'assistant', content: response });
    }
    result.push(response);
    console.log(`[User]----------------------------------------\n${text}\n[Assistant]----------------------------------------\n${response}`);
  }
  return result;
};

export {
  LLMOptions,
  chatTask,
  ModeGenerate,
};
