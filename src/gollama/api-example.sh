#!/bin/sh

# example of using the gollama API from cURL
curl \
	-X POST \
	-F 'source_language=chinese' \
	-F 'target_language=english' \
	-F 'model=mixtral:instruct' \
	-F 'file=@test.docx' \
	-F 'options="temperature:0.0,context:1024"' \
	127.0.0.1:8080/translate
