import { checkProgram, exec } from './shell';
import { curryWrap } from './curry';

const IMAGE = 'ollama/ollama:0.1.22';
const GPU = 'NVIDIA-A10';

type PodOptions = {
  num: number,
  name: string,
  image: string,
  gpu?: string,
  command: string[],
  port?: number,
  standby?: boolean,
};

const podName = (i: number, options: { num: number, name: string }) => options.num > 1
    ? `${options.name}-pod-${i}`
    : `${options.name}-pod`;

const serviceName = (i: number, options: { num: number, name: string }) => options.num > 1
    ? `${options.name}-${i}`
    : `${options.name}`;

const webName = (i: number, options: { num: number, name: string }) => options.num > 1
    ? `${options.name}-${i}-dcct.nrp-nautilus.io`
    : `${options.name}-dcct.nrp-nautilus.io`;

const pod = (i:number, options: PodOptions) => {
  const name = podName(i, options);
  return {
    apiVersion: 'v1',
    kind: 'Pod',
    metadata: {
      name,
      labels: { 'k8s-app': name }
    },
    spec: {
      containers: [
        {
          image: options.image,
          name: name,
          command: options.command || undefined,
          // command: ['/bin/sh', '-c', 'sleep 30'],
          resources: {
            limits: {
              cpu: '2',
              memory: '8Gi',
              'nvidia.com/gpu': '1'
            }
          },
          env: [
            {
              name: 'PATH',
              value: '/usr/local/nvidia/bin:/usr/local/cuda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
            },
            {
              name: 'LD_LIBRARY_PATH',
              value: '/usr/local/nvidia/lib:/usr/local/nvidia/lib64'
            },
            {
              name: 'NVIDIA_DRIVER_CAPABILITIES',
              value: 'compute,utility'
            }
          ],
        }
      ],
      affinity: options.gpu ? {
        nodeAffinity: {
          requiredDuringSchedulingIgnoredDuringExecution: {
            nodeSelectorTerms: [{
                matchExpressions: [{
                    key: 'nvidia.com/gpu.product',
                    operator: 'In',
                    values: [ options.gpu ]
                  }
                ]}
            ]}
        }
      } : undefined
    }
  };
};

const service = (i:number, options: PodOptions) => {
  const name = serviceName(i, options);
  return {
    apiVersion: 'v1',
    kind: 'Service',
    metadata: {
      name,
      labels: { 'k8s-app': name }
    },
    spec: {
      type: 'ClusterIP',
      ports: [{ port: 80, targetPort: options.port || 80 }],
      selector: { 'k8s-app': podName(i, options) }
    }
  };
};

const ingress = (i:number, options: PodOptions) => {
  const name = serviceName(i, options);
  return {
    apiVersion: 'networking.k8s.io/v1',
    kind: 'Ingress',
    metadata: {
      name,
      annotations: { 'kubernetes.io/ingress.class': 'haproxy' }
    },
    spec: {
      rules: [{
        host: webName(i, options),
        http: {
          paths: [{
            path: '/',
            pathType: 'ImplementationSpecific',
            backend: {
              service: {
                name,
                port: { number: 80 }
              }
            }
          }]
        }
      }],
      tls: [{ hosts: [webName(i, options)] }]
    }
  };
};

const getPodsStatus = async (pods: PodOptions) => {
  const response = await exec`kubectl get pod`;

  const res = response
    .trim()
    .split('\n')
    .map(line => line.split(/\s+/))
    .filter(podName => podName[0].includes(pods.name))
    .map(podName => podName[2]);

  if (res.length === 0)
    return Array(pods.num).fill('NotFound');
  return res;
}

const waitPodUntilReady = async (i, pods: PodOptions) => {
  while (true) {
    const podsStatus = await getPodsStatus(pods);
    if (podsStatus[i] === 'NotFound')
      return Promise.reject('Pod not found');
    if (podsStatus[i] === 'Running')
      return;
    await new Promise(resolve => setTimeout(resolve, 3000));
  }
}

const randUUID = () =>
  'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });

const checkAvailability = async (options: PodOptions) => {
  const response = await fetch(
    'https://portal.nrp-nautilus.io/rpc',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'guest.ListNodeInfo',
        params: {},
        // random uuid
        id: randUUID()
      })
    }
  );
  const json = await response.json();
  if (json.error)
    return Promise.reject(json.error);
  
  return json.result.Nodes
    .filter(node => options.gpu ? node.GPUType === options.gpu : true)
    .filter(node => node.Taints.length === 0)
    .map(node => +(node.GPUAvailable))
    .reduce((a, b) => a + b, 0);
}

const upKubernetes = (options: PodOptions) => async () => {
  console.log('Preparing kubernetes resources');

  const available = await checkAvailability(options);
  if (available < options.num)
    return Promise.reject('Not enough resources');

  const podsStatus = await getPodsStatus(options);
  await Promise.all(
    podsStatus.map(async (status, i) => {
      const pod_i = pod(i, options);
      const pod_name = podName(i, options);

      if (status !== 'Running') {
        if (status !== 'NotFound') {
          await exec`kubectl delete pod ${pod_name}`;
        }
        if (status !== 'Pending' || status !== 'Waiting') {
          console.log(`Creating pod ${pod_name}`);
          const pod_script = new Response(JSON.stringify(pod_i));
          await exec`kubectl create -f - < ${pod_script}`;
        }
        console.log(`Waiting ${pod_name}`);
        await waitPodUntilReady(i, options);

        const service_i = service(i, options);
        const service_script = new Response(JSON.stringify(service_i));
        await exec`kubectl create -f - < ${service_script}`;

        const ingress_i = ingress(i, options);
        const ingress_script = new Response(JSON.stringify(ingress_i));
        await exec`kubectl create -f - < ${ingress_script}`;

        console.log('Cold start, waiting for 10 seconds');
        await new Promise(resolve => setTimeout(resolve, 10000));
      }
      console.log(`Pod ready: ${pod_name}`);
    })
  );
}

const downKubernetes = (options: PodOptions) => async () => {
  if (options.standby) {
    console.log('Standby mode, skipping cleanup');
    return;
  }
    
  console.log('Cleaning up kubernetes resources');
  await Promise.all(
    Array.from({ length: num }, (_, i) => i + 1)
    .map(async i => {
      const name = podName(i, options);
      console.log(`Deleting pod ${name}`);
      await exec`kubectl delete pod ${name}`;
    })
  );
}

const useKubernetes = curryWrap(
  upKubernetes,
  downKubernetes
);

export {
  useKubernetes,
  webName,
};
