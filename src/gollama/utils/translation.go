package utils

// Handles the translation of text
// Makes http requests to the ollama api
// Returns a string of translated text

// Author: Korben Tompkin

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
)

// Struct to hold the response from the ollama api
type Response struct {
	Response string `json:"response"`
}

// Translate a string of text
func Translate(text string, sourceLanguage string, targetLanguage string, customPrompt string) (string, error) {
	// Array of response strings
	var responses []string

	// Prompt to be sent to the ollama api
	var prompt string

	// Format the prompt with the source and target languages if no custom prompt is provided
	if customPrompt == "" {
		prompt = fmt.Sprintf("Translate the following %s text into academic %s, focusing on preserving the content, tone, and sentiment. Do not include any discussion, provide only the translated text: \n\n%s", sourceLanguage, targetLanguage, text)
	} else {
		prompt = fmt.Sprintf("%s \n\n%s", customPrompt, text)
	}

	// Create the request url
	url := "http://127.0.0.1:11434/api/generate/"

	// Format the request body
	data, err := json.Marshal(map[string]string{
		"model":  "llama2",
		"prompt": prompt,
	})
	if err != nil {
		return "", err
	}

	// Create the request
	req, err := http.NewRequest("POST", url, strings.NewReader(string(data)))
	if err != nil {
		return "", err
	}

	// Set the request headers
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	// Send the request
	client := &http.Client{}

	// Read the first response so we can get the status code
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}

	reader := bufio.NewReader(resp.Body)
	for {
		line, err := reader.ReadBytes('\n')
		if err != nil {
			if err == io.EOF {
				break
			}
			return "", err
		}

		// unmarshal the response
		var response Response
		err = json.Unmarshal(line, &response)
		if err != nil {
			return "", err
		}

		// Add the response to the array
		responses = append(responses, response.Response)
	}

	// turn the response into a string
	result := strings.Join(responses, "")

	// Return the translated text
	return result, nil
}