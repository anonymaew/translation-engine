from .kube import Pod
from .doctext import is_nothing
from dotenv import load_dotenv
import os
import openai
from openai import OpenAI
import requests
from time import sleep


# checking whether the machine has the model
def model_check(pod, model):
    try:
        assert pod.exec_code('ollama', 'show', model, '--license') == 0
    except Exception:
        print(f'Model {model} not found, pulling...')
        pod.exec_code('ollama', 'pull', model)


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
        while i < len(jobs):
            job = jobs[i]
            if is_nothing(job):
                result.append('')
                i += 1
                continue
            messages = [
                {'role': 'system', 'content': llm['prompt']},
                {'role': 'user', 'content': job}
            ]
            try:
                res = self.job(messages, llm)
                if 'validation' in llm and llm['validation'](job, res) is False:
                    # print(res)
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
            finally:
                i += 1
        self.cleanup()
        return result

    def cleanup(self):
        pass

    def stop(self):
        pass


class OllamaAgent(ChatAgent):
    def __init__(self, pod_options):
        self.pod = Pod(pod_options)
        self.pod_options = pod_options
        super().__init__()
        self.start()
        self.server = None

    def start(self):
        self.pod.up()

    def prepare(self, llm):
        model_check(self.pod, llm['model'])
        self.pod.port_forward(11434)
        self.server = 'http://localhost:11434'

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
                timeout=45
            )
            return res.json()['message']['content'].strip()
        except requests.exceptions.Timeout:
            raise requests.exceptions.Timeout

    def cleanup(self):
        # self.port_forwarding.stop()
        if not self.pod_options['standby']:
            self.pod.delete()
            while self.pod.status() is not None:
                sleep(1)


class OpenAIAgent(ChatAgent):
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        super().__init__()

    def error_handler(self, e):
        if isinstance(e, openai.RateLimitError):
            print('OpenAI rate limit reached, waiting for 65 seconds...')
            sleep(65)
        else:
            raise e

    def job(self, messages, llm):
        res = self.client.create_completion(
            model=llm['model'],
            messages=messages,
            temperature=llm['options']['temperature'],
        )
        return res.choices[0].message.content.strip()
