from .kube import restart_kubernetes
import requests
from time import sleep


def is_nothing(text):
    return text == '' or text == '\n' or text == '\n\n'


# checking whether the machine has the model
def model_check(pod, model):
    try:
        pod.exec(['ollama', 'show', model])
    except Exception:
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


def chat_task(pod, llm, jobs):
    model_check(pod, llm['model'])

    port_forwarding = pod.portforward(remote_port=11434)
    port_forwarding.start()
    sleep(1)
    server = f'http://localhost:{port_forwarding.local_port}'

    i, result = 0, []
    while i < len(jobs):
        job = jobs[i]
        if is_nothing(job):
            result.append('')
        messages = [
            {'role': 'system', 'content': llm['prompt']},
            {'role': 'user', 'content': job}
        ]
        try:
            res = chat_job(server, llm, messages)
            if 'validation' in llm and llm['validation'](res) is False:
                print('Result validation failed, retrying...')
                i -= 1
                continue
            result.append(res)
            print('[User]----------------------------------------')
            print(job)
            print('[Assistant]-----------------------------------')
            print(res)
        except requests.exceptions.Timeout:
            print('LLM server hung up, restarting...')
            restart_kubernetes(pod)
            i -= 1
            continue
        finally:
            i += 1

    port_forwarding.stop()
    return result
