#!/bin/sh

# function fetching models
ollama_pull() {
	sleep 1
	< models.txt xargs -I{} ollama pull {}
}

# ollama serve & ollama_pull & /gollama/gollama
/gollama/gollama
