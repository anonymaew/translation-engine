# Research Logs by Napat Srichan

## The use of Kubernetes and GPU

Kubernetes allows me to access one of the most powerful GPU in the world,
[NVIDIA A100](https://www.nvidia.com/en-us/data-center/a100/), for AI
inference. Using the local inference architecture compared to OpenAI's GPT-4
from ChatGPT's api, we can translate the entire book under 20 minutes compared
to 6 hours from ChatGPT using this kind of GPU.

Interestingly, although the LLM model with 7 billion parameters requires only
around 6GB of GPU VRAM, the architecture of the GPU still matters the most. For
example, running the LLM on `NVIDIA-GeForce-GTX-1080-Ti` with 12GB of VRAM is
10 times slower than the flagship `NVIDIA A100-SXM4-80GB` with 80GB of VRAM,
and both utilize GPU by the same 6GB. This makes the NVIDIA A100 the best
choice for running the LLM model, but also leaves most of the VRAM and
computational power unutilized.

### Hiccups on reserving the GPU

Currently, there are around 20 nodes in the cluster that equipped with NVIDIA
A100, each with 4-8 cores of GPU available. Although the cluster seems to have
a lot of space available for us, the entire cluster have the high demand for
this specific kind of GPU and leave few spots available.

Moreover, some nodes have quite old GPU drivers that are incompatile with our
program. This also leaves even fewer choice of nodes. However, this can be
solved by forcing the program to use the specific CUDA version. If the CUDA
version is too old, the program may not run. If the CUDA version is too new,
the program may not detect the GPU that has older driver version. The current
CUDA version that seems to work reliably right now is `11.7.1`.

The tip to deploying on kubernetes smoothly is to:

- Observes available nodes that has `NVIDIA A100` GPU and some RAMs and CPU
  available. Using the [resource
  portal](https://portal.nrp-nautilus.io/resources) helps
- Quickly grab an available space by specifying the GPU type on the kubernetes
  playbook. Sometimes, if we want more specific node, we can also specify the
  node we want (in case some nodes have weird GPU driver version)
  ```yaml
  # on pod spec
  affinity:
   nodeAffinity:
     requiredDuringSchedulingIgnoredDuringExecution:
       nodeSelectorTerms:
       - matchExpressions:
        # specify GPU here 
         - key: nvidia.com/gpu.product
           operator: In
           values:
           - NVIDIA-A100-SXM4-80GB
        # specify the node here
         - key: kubernetes.io/hostname
           operator: In
           values:
           - node-1-1.sdsc.optiputer.net
  ```
- In an unlikely case, if the node we want has the taint limitation, we can add
  the taint to the pod spec (so that the pod qualifies to run on the node)
  ```yaml
  # on pod spec
  tolerations:
  - key: "nautilus.io/nrp-testing"
    operator: "Exists"
    effect: "NoSchedule"
  ```
  (not sure if this breaks the rules or not, sometimes it works. So use with
  care and I am not guaranteed for the result)

## Running the program

The current workflow of the program is:

1. Convert the document from `docx` to `md` using `pandoc`
2. Split the document into smaller chunks, by paragraph (detecting `\n\n`)
3. Inferencing LLM using the prompt constructed from the instruction with the
   paragraph
4. Recombine the result into a single document
5. Convert the document from `md` back to `docx` using `pandoc`

I currently use JavaScript for this task as it is the fast-paced prototyping
language, which is suitable for this kind of task. Go is fine, but I will plan
to switch to Go towards the end of the project and the production phase.

### Result between `llama2` and `mistral` model

[`llama2`](https://ai.meta.com/llama/) is the open-source model from Meta. It
has `7B`, `13B`, and `70B` parameters version. Each also has `text` and `chat`
variant (default to `chat`). Here is the observation of the result (between
`llama2:7B` and `llama2:70B`):

- obviously, `llama2:70B` spent more time than `llama2:7B` for the same task (2
  hours vs 20 minutes). `llama2:70B` uses 40GB compared to 6GB from `llama2:7B`
  to process.
- `llama2:7B` is more likely to leave some text untranslated compared to
  `llama2:70B`. It is may be of how smaller model cannot handle the large
  context and leaves things unchanged.
- `llama2:70B` leaves considerably more details and elaboration in translation.

[`mistral`](https://mistral.ai/news/announcing-mistral-7b/) is the open-source
model from Mistral company that claims to be better than `llama2` at `7B`parameters.
Here is the observation of the result (between `llama2:7B` and `mistral:7B`):

- `llama2` tends to leave artifacts (unwanted chat conversation piece) in the
  translation, especially on shorter chunks of text. For example
  ```txt
  Here is the translation of the text:
  ....(translated text)....
  I hope this helps. If you have any questions, please let me know.
  ```
  This might be due to how the basic variant of `llama2` is fine-tuned on chat
  conversation. However, larger chunks of text is less likely to have artifacts.
- `mistral` does not leave any artifacts in the translation. Interestingly,
  it leaves some notes in the translation if it detects that the translation
  might need more context, or the footnote is missing.
  ```txt
  ....(translated text)....
  [Note: the translation contains footnotes that are not included in the
  original text, and the result may be incomplete due to the lack of context.]
  ```
  However, this may be removed manually or by specifying on the prompt.
- `mistral` keeps the markdown syntax in the translation result text, compared
  to `llama2` that mostly-clean all markdown syntax.
- Sometimes, `mistral` hallucinate the short chunk of text with unintentional
  explanations. The worst case is the title translation, which `mistral`
  includes abstractions, keywords, and introduction only from the short title
  name.

### Attemp on increasing the performance

As one instance of the LLM model use 6GB of VRAM, I tried to run multiple of
them on one single GPU for full utilization. However, when it comes to the
performance, the total throughput is still the same with a single instance.
This might be due to the memory bandwidth bottleneck between the GPU and the
CPU for this LLM inferencing architecture, which leads to the slowdown of the
output. Therefore, we still have to run one model instance per GPU.

### Weird bug encouters

So far, on every model, every time, there is always at least one paragraph of
the text that when combining into a prompt, makes the model hangs indefinitely.
This is not due to the too large context size as the problematic paragraph is
not the longest one. The larger chunk of text runs fine too.

One temporary quick fix is to timeout the model after waiting longer than
typical inference time (depends on each GPU) and return empty string. This is
not good as the result text may lose some paragraphs.

One observation right now on all those problematic paragraphs is that they
usually contain a large amount of names, which might cause some problem in
terms of translation. The next fix might be to detect the name and use those
information to further prompt the model carefully.

## TODO

- [ ] try `llama2:text` variant
- [ ] capturing the name and use it to prompt the model
  - [ ] methods and prompts for extracting the name and specifics
  - [ ] combining to prompt for translation
