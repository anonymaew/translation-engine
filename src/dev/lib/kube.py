import requests
from uuid import uuid4
from time import sleep
import json
import subprocess
import os


class Pod:
    def __init__(self, options):
        self.options = options
        self.name = f'{options["name"]}-pod'
        self.json = pod_json(options, self.name)

    def status(self):
        res = subprocess.run(['kubectl', 'get', 'pod', self.name,
                              '--template={{printf "%s" .status.phase}}'],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL).stdout.decode('utf-8').strip()
        return None if res == '' else res

    def check_spec(self):
        response = requests.post(
            'https://portal.nrp-nautilus.io/rpc',
            json={
                'jsonrpc': '2.0',
                'method': 'guest.ListNodeInfo',
                'params': {},
                'id': str(uuid4()),
            },
        )
        json = response.json()
        if 'error' in json:
            raise Exception(json['error']['message'])
            gpu_needs = list(filter(
                lambda n: 'gpu' not in self.options or n['GPUType'] == self.options['gpu'],
                json['result']['Nodes']))
            # print(list(map(lambda n: n['Taints'], gpu_needs)))
            # no_taint_nodes = list(filter(
            #     lambda n: n['Taints'] is None or n['Taints'] == [], gpu_needs))
            gpus = list(map(lambda n: int(n['GPUAvailable']), gpu_needs))
            return sum(gpus)

    def up(self):
        print('Preparing kubernetes resources')
        available = self.check_spec()
        if available == 0:
            raise Exception(f'Not enough resources: {self.options["gpu"]}')

        status = self.status()
        if status != 'Running':
            if status in ['Completed', 'Failed', 'Error']:
                subprocess.run(['kubectl', 'delete', 'pod',
                                self.name])
                while self.status() is not None:
                    sleep(1)
            if status not in ['Pending', 'ContainerCreating', 'Waiting']:
                print(f'Creating {self.name}')
                subprocess.run(['kubectl', 'create', '-f', '-'],
                               input=self.json, text=True)

            print(f'Waiting for {self.name} to be ready')
            while self.status() != 'Running':
                sleep(1)

        print(f'Pod ready: {self.name}')

    def exec_code(self, *command):
        res = subprocess.run(['kubectl', 'exec', self.name, '--', *command],
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return res.returncode

    def port_forward(self, port):
        id = os.fork()
        if id == 0:
            res = subprocess.run(['kubectl', 'port-forward', f'pod/{self.name}',
                                  f'{port}'], stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        else:
            # while requests.get(f'http://localhost:{port}').status_code != 200:
            while True:
                try:
                    requests.get(f'http://localhost:{port}')
                    break
                except requests.exceptions.ConnectionError:
                    sleep(1)
                except requests.exceptions.Timeout:
                    print('Timeout')
                    pass
            print(f'Server accessible at http://localhost:{port}')
            os.kill(id, 9)

    def down(self):
        if self.status() is not None and not self.options['standby']:
            print(f'Deleting {self.name}')
            subprocess.run(['kubectl', 'delete', 'pod',
                            self.name])
            while self.status() is not None:
                sleep(1)


def pod_json(options, name):
    return json.dumps({
        'apiVersion': 'v1',
        'kind': 'Pod',
        'metadata': {
            'name': name,
                'labels': {
                    'k8s-app': name,
                },
        },
        'spec': {
            'containers': [
                {
                    'name': name,
                    'image': options['image'],
                    'command': [] if 'command' not in options else options['command'],
                    'resources': {
                        'limits': {
                            'cpu': '2',
                            'memory': '8Gi',
                            'nvidia.com/gpu': '1',
                        },
                    },
                    # 'volumeMounts': [{
                    #     'mountPath': '/usr/share/ollama',
                    #     'name': 'data',
                    # }],
                    'env': [
                        {
                            'name': 'PATH',
                            'value': '/usr/local/nvidia/bin:/usr/local/cuda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
                        },
                        {
                            'name': 'LD_LIBRARY_PATH',
                            'value': '/usr/local/nvidia/lib:/usr/local/nvidia/lib64'
                        },
                        {
                            'name': 'NVIDIA_DRIVER_CAPABILITIES',
                            'value': 'compute,utility'
                        },
                    ],
                },
            ],
            # 'volumes': [{
            #     'name': 'data',
            #     'persistentVolumeClaim': {
            #         'claimName': 'ollama-models'
            #     }
            # }],
            'affinity': {
                'nodeAffinity': {
                    'requiredDuringSchedulingIgnoredDuringExecution': {
                        'nodeSelectorTerms': [
                            {
                                'matchExpressions': [
                                    {
                                        'key': 'nvidia.com/gpu.product',
                                        'operator': 'In',
                                        'values': [options['gpu']],
                                    },
                                ],
                            },
                        ],
                    },
                },
            } if 'gpu' in options else {},
        },
    })


if __name__ == '__main__':
    res = subprocess.run(['kubectl', 'port-forward', f'pod/translate-pod',
                          '11434'],
                         stderr=subprocess.DEVNULL)
    print('done')
    sleep(100)
