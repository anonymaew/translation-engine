package utils

// Helper function to translate a string of text
// Makes http requests to the ollama api
// Returns a string of translated text

import (
	"encoding/json"
	"io"
	"net/http"
	"strings"
)

// Translate a string of text
func Translate(text string) (string, error) {
	// Create the request url
	url := "http://127.0.0.1:11434/api/generate/"

	// Format the request body
	data, err := json.Marshal(map[string]string{
		"model":  "llama2",
		"prompt": text,
		"stream": "false",
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

	// wg := sync.WaitGroup{}

	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}

	body, err := readBody(resp)
	if err != nil {
		return "", err
	}

	temp, err := decodeBody(body)
	if err != nil {
		return "", err
	}

	response := temp["response"].(string)

	// for resp.StatusCode == 307 {
	// 	// Read the response body
	// 	wg.Add(1)
	// 	go func() {
	// 		defer wg.Done()
	// 		resp, err = client.Do(req)
	// 		if err != nil {
	// 			return
	// 		}
	// 		body, err := readBody(resp)
	// 		if err != nil {
	// 			return
	// 		}
	// 		temp, err := decodeBody(body)
	// 		if err != nil {
	// 			return 
	// 		}
	// 		response += temp["response"].(string)
	// 	}()
	// 	wg.Wait()
	// }

	// Return the translated text
	return response, nil
}

// Read the response body
func readBody(resp *http.Response) (string, error) {
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}

	return string(body), nil
}

// Decode the response body
func decodeBody(body string) (map[string]interface{}, error) {
	var result map[string]interface{}

	err := json.Unmarshal([]byte(body), &result)
	if err != nil {
		return nil, err
	}

	return result, nil
}
