from .kube import restart_kubernetes, pod_obj
import openai
import requests
from time import sleep
from .doctext import is_nothing
from dotenv import load_dotenv
import os
from openai import OpenAI


# checking whether the machine has the model
def model_check(pod, model):
    try:
        pod.exec(['ollama', 'show', model])
    except Exception:
        print(f'Model {model} not found, pulling...')
        pod.exec(['ollama', 'pull', model])


def chat_job(server, llm, messages):
    body = {
        'messages': messages,
        'options': llm['options'],
        'model': llm['model'],
        'stream': False
    }
    try:
        res = requests.post(
            f'{server}/api/chat',
            json=body,
            timeout=45
        )
        return res.json()['message']['content'].strip()
    except requests.exceptions.Timeout:
        return requests.exceptions.Timeout


class ChatAgent:
    def __init__(self, llm):
        self.llm = llm

    def start(self):
        pass

    def prepare(self):
        pass

    def job(self, messages):
        pass

    def error_handler(self, e):
        raise e

    def task(self, jobs):
        self.prepare()
        i, result = 0, []
        while i < len(jobs):
            job = jobs[i]
            if is_nothing(job):
                result.append('')
                i += 1
                continue
            messages = [
                {'role': 'system', 'content': self.llm['prompt']},
                {'role': 'user', 'content': job}
            ]
            try:
                res = self.job(messages)
                if 'validation' in self.llm and self.llm['validation'](job, res) is False:
                    print('Result validation failed, retrying...')
                    i -= 1
                    continue
                result.append(res)
                print('[User]----------------------------------------')
                print(job)
                print('[Assistant]-----------------------------------')
                print(res)
            except Exception as e:
                self.error_handler(e)
                i -= 1
                continue
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
    def __init__(self, pod_options, llm_options):
        self.pod = pod_obj(pod_options)
        self.pod_options = pod_options
        self.port_forwarding = None
        super().__init__(llm_options)
        self.start()
        self.server = None

    def start(self):
        exists = self.pod.exists()
        if exists:
            self.pod.patch(self.pod_options)
        else:
            self.pod.create()
        self.pod.wait('condition=Ready')
        if not exists:
            print('Cold start, waiting for 5 seconds')
            sleep(5)
        print(f'Pod ready: {self.pod_options["name"]}')

    def prepare(self):
        model_check(self.pod, self.llm['model'])
        self.port_forwarding = self.pod.portforward(remote_port=11434)
        self.port_forwarding.start()
        sleep(1)
        self.server = f'http://localhost:{self.port_forwarding.local_port}'
        print(f'Port forwarding ready: {self.server}')

    def error_handler(self, e):
        if e == requests.exceptions.Timeout:
            print('LLM server hung up, restarting...')
            self.stop()
            self.start()
        else:
            raise e

    def job(self, messages):
        body = {
            'messages': messages,
            'options': self.llm['options'],
            'model': self.llm['model'],
            'stream': False
        }
        try:
            res = requests.post(
                f'{self.server}/api/chat',
                json=body,
                timeout=45
            )
            return res.json()['message']['content'].strip()
        except requests.exceptions.Timeout:
            return requests.exceptions.Timeout

    def cleanup(self):
        self.port_forwarding.stop()
        if not self.pod_options['standby']:
            self.pod.delete()
            self.pod.wait('deletion')


class OpenAIAgent(ChatAgent):
    def __init__(self, llm_options):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        super().__init__(llm_options)

    def error_handler(self, e):
        if isinstance(e, openai.RateLimitError):
            print('OpenAI rate limit reached, waiting for 65 seconds...')
            sleep(65)
        else:
            raise e

    def job(self, messages):
        res = self.client.create_completion(
            model=self.llm['model'],
            messages=messages,
            temperature=self.llm['options']['temperature'],
        )
        return res.choices[0].message.content.strip()
