#!/bin/sh

# example of using the gollama API from cURL
curl \
	-X POST \
	-F 'source_language=chinese' \
	-F 'target_language=english' \
	-F 'model=llama2' \
	-F 'file=@chinese.docx' \
	localhost:8080/translate
