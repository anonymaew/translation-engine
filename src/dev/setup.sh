#!/bin/sh

# kubectl get pod -o custom-columns=name:metadata.name --no-headers | \
#   xargs -I{} kubectl exec -it {} -- /bin/bash -c 'curl localhost:11434/api/pull -d "{\"name\":\"mistral\"}"'
#
# kubectl get pod -o custom-columns=name:metadata.name --no-headers | \
#   parallel kubectl exec -it {} -- /bin/bash -c 'nvidia-smi dmon -c 1 -s u | tail -n 1'

NUM_PODS=8
IMAGE='ollama\/ollama:0.1.16'
# IMAGE='nsrichan\/ai4humanities-translation-engine:dev@sha256:837a3d25b6c1e0a3b79947be5d00c4e4a4c5fd3329192b297cfaed14ea16b35b'
GPU='NVIDIA-A10'
# GPU='NVIDIA-A100-SXM4-80GB'
# NODE='gpu-08.nrp.mghpcc.org'

sed "s/<IMAGE>/${IMAGE}/g" deploy-template.yml | \
  # sed "s/<NODE>/${NODE}/g" | \
  sed "s/<GPU>/${GPU}/g" > \
  "deploy-template-temp.yml"

seq 1 ${NUM_PODS} | \
  parallel -I{} '''
    sed "s/<NUM>/{}/g" deploy-template-temp.yml
    ''' > \
  "deploy-${NUM_PODS}.yml"

rm deploy-template-temp.yml
     
kubectl create -f "deploy-${NUM_PODS}.yml"
