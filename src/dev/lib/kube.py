from .curry import curry_wrap
from kr8s.objects import Pod
import requests
from uuid import uuid4
from time import sleep


def pod_name(options):
    return f'{options["name"]}-pod'


def service_name(options):
    return f'{options["name"]}'


def web_name(options):
    return f'{options["name"]}-dcct.nrp-nautilus.io'


def pod_obj(options):
    name = pod_name(options)
    return Pod({
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
                        }
                    ],
                },
            ],
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


def rand_uuid():
    return str(uuid4())


def check_availability(options):
    response = requests.post(
        'https://portal.nrp-nautilus.io/rpc',
        json={
            'jsonrpc': '2.0',
            'method': 'guest.ListNodeInfo',
            'params': {},
            'id': rand_uuid(),
        },
    )
    json = response.json()
    if 'error' in json:
        raise Exception(json['error']['message'])

    gpu_needs = list(filter(
        lambda n: 'gpu' not in options or n['GPUType'] == options['gpu'], json['result']['Nodes']))
    no_taint_nodes = list(filter(
        lambda n: n['Taints'] is None or n['Taints'] == [], gpu_needs))
    gpus = list(map(lambda n: int(n['GPUAvailable']), no_taint_nodes))
    return sum(gpus)


def up_kubernetes(config):
    def f(_):
        options = config[0]
        print('Preparing kubernetes resources')
        # available = check_availability(options)
        # if available == 0:
        #     raise Exception('Not enough resources')

        pod = pod_obj(options)
        exists = pod.exists()

        if exists:
            pod.patch(options)
        else:
            pod.create()
        pod.wait('condition=Ready')

        if not exists:
            print('Cold start, waiting for 10 seconds')
            sleep(10)

        print(f'Pod ready: {pod_name}')
    return f


def down_kubernetes(config):
    def f(_):
        options = config[0]
        pod = pod_obj(options)
        if pod.exists() and not options['standby']:
            pod.delete()
            pod.wait('deletion')
    return f


use_kubernetes = curry_wrap(up_kubernetes, down_kubernetes)


def restart_kubernetes(options):
    print('Restarting kubernetes resources')
    down_kubernetes(options)()
    up_kubernetes(options)()
