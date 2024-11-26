from .kube import Pod, port_forward
from .doctext import is_nothing
from dotenv import load_dotenv
import os
import openai
from openai import OpenAI
import requests
from time import sleep


# checking whether the machine has the model
def model_check(server, llm):
    models = requests.get(f'{server}/api/tags').json()['models']
    wanted_model = list(
        filter(lambda model: model['name'] == llm['model'], models))
    print(wanted_model)
    if (len(wanted_model) > 0):
        return
    print(f'Model {llm['model']} not found, pulling...')
    # if 'huggingface_link' in llm:
    #     pod.exec_code('apt', 'install', 'curl', '-y')
    #     real_link = llm['huggingface_link'].replace('blob', 'resolve')
    #     filepath = f'/models/{real_link.split('/')[-1]}'
    #     pod.exec_code('curl', '-L', real_link +
    #                   '?download=true', '-o', filepath)
    #     pod.exec_code('curl', 'localhost:11434/api/create', '-d',
    #                   '{' + f'"name": "{llm['model']}", "modelfile": "FROM {filepath}"' + '}')
    # else:
    #     pod.exec_code('ollama', 'pull', llm['model'])
    res = requests.post(
        f'{server}/api/pull',
        json={'model': llm['model'], 'stream': False},
    )
    # return res.json()['message']['content']


def prime_to_array(prime):
    if len(prime) % 2 != 0:
        raise ValueError('Prompting shots must be even: user, assistant')
    return [{'role': ['user', 'assistant'][i % 2], 'content': p} for i, p in enumerate(prime)]


class ChatAgent:
    def __init__(self):
        pass

    def start(self):
        pass

    def job(self, messages, llm):
        pass

    def error_handler(self, e):
        raise e

    def task(self, jobs, llm):
        i, result = 0, []
        print('Starting batch task')
        while i < len(jobs):
            job = jobs[i]
            if is_nothing(job):
                result.append('')
                i += 1
                continue
            user_text = llm['user_prompt'](
                job) if 'user_prompt' in llm else job
            messages = [{'role': 'system', 'content': llm['prompt'] if 'prompt' in llm else ''}] + \
                (prime_to_array(llm['prime']) if 'prime' in llm else []) + \
                [{'role': 'user', 'content': user_text}]
            try:
                res = self.job(messages, llm)
                if 'validation' in llm and llm['validation'](job, res) is False:
                    print(res)
                    print('Result validation failed, retrying...')
                    i -= 1
                    continue
                result.append(res)
                print('[User]----------------------------------------')
                print(user_text)
                print('[Assistant]-----------------------------------')
                print(res)
            except Exception as e:
                self.error_handler(e)
                i -= 1
                continue
            finally:
                i += 1
        self.cleanup()
        return result

    def cleanup(self):
        pass

    def stop(self):
        pass


class OllamaAgent(ChatAgent):
    def __init__(self):
        # self.pod = Pod({**pod_options, **{'data': True}})
        # self.pod_options = pod_options
        super().__init__()
        self.start()
        self.server = None

    def start(self):
        pass
        # self.pod.up()

    def prepare(self, llm):
        port_forward('ollama', 11434)
        self.server = 'http://localhost:11434'
        model_check(self.server, llm)

    def error_handler(self, e):
        if e == requests.exceptions.Timeout:
            print('LLM server hung up, restarting...')
            self.stop()
            self.start()
        else:
            raise e

    def task(self, jobs, llm):
        self.prepare(llm)
        return super().task(jobs, llm)

    def job(self, messages, llm):
        body = {
            'messages': messages,
            'options': llm['options'],
            'model': llm['model'],
            'stream': False
        }
        try:
            res = requests.post(
                f'{self.server}/api/chat',
                json=body,
            )
            return res.json()['message']['content']
        except requests.exceptions.Timeout:
            raise requests.exceptions.Timeout

    def cleanup(self):
        pass
        # self.port_forwarding.stop()
        # if not self.pod_options['standby']:
        #     self.pod.delete()
        #     while self.pod.status() is not None:
        #         sleep(1)


class OpenAIAgent(ChatAgent):
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        super().__init__()

    def error_handler(self, e):
        # if isinstance(e, openai.RateLimitError):
        #     print('OpenAI rate limit reached, waiting for 65 seconds...')
        #     sleep(65)
        # else:
        raise e

    def job(self, messages, llm):
        res = self.client.chat.completions.create(
            model=llm['model'],
            messages=messages,
            temperature=llm['options']['temperature'],
        )
        return res.choices[0].message.content.strip()
