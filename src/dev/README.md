# LLM Document Translation using Kubernetes worker

This program will translate a given document using [open source large language
model](https://ollama.com/library) with the computation power on a Kubernetes
cluster.

## How this program works

- Manipulating document files and dissecting texts locally on the machine.
- Spin up Kubernetes pods by itself according to the job.
- Translation is sent to the pods to be processed using configured prompts.

## Prerequisites

1. [Python3](https://www.python.org/downloads/): Python (preferably 3.11+)
2. [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/):
   Kubernetes cluster manager
3. Access to a Kubernetes cluster, preferably with [NRP Nautilus cluster](https://portal.nrp-nautilus.io/).
4. [pandoc](https://pandoc.org/): for converting documents

## Running the program

1. Put the document to be translated in this directory.
2. Adjusting parameters in `main.py` file accordingly.
3. Run the program using `python main.py` or `python3 main.py`.
4. If success, the translated document will be in the same directory with the
   suffix `-translated`.
