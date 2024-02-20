package main

// The main file for the program
// Author: Korben Tompkin

// The following program is middleware for a translation engine
// Powered by Large Language Models installed with ollama
// The program accepts a .docx file and translates it into another language
// The engine runs inside of a docker container
// The model API is exposed on port 11434
// The engine accepts text via a POST request to /api/generate
// The engine returns a JSON stream of the translated text

import (
	"crypto/rand"
	"fmt"
	"io"
	"log"
	"math/big"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"translation-engine/src/gollama/utils"
)

const (
	BASE_URL = "http://127.0.0.1"                                               // The base url for the server
	PORT     = ":8080"                                                          // The port for the server
	CHARS    = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" // The characters to use for the random string
	LENGTH   = 10                                                               // The length of the random string
)

type TranslateDocumentRequest struct {
	SourceLanguage string `json:"source_language"`
	TargetLanguage string `json:"target_language"`
	CustomPrompt   string `json:"custom_prompt"`
	Model          string `json:"model"`
}

func main() {
	// Initialize the server
	http.HandleFunc("/translate", translateDocumentHandler)
	http.HandleFunc("/download", downloadHandler)
	http.ListenAndServe(PORT, nil)

	// Exit the program
	os.Exit(0)

}

func translateDocumentHandler(w http.ResponseWriter, r *http.Request) {
	// Create an ELF compliant logger
	// Log the time, date, and file name
	logger := log.New(os.Stdout, "INFO: ", log.Ldate|log.Ltime|log.Lshortfile)

	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Parse the form data including the file and the JSON data
	err := r.ParseMultipartForm(10 << 20) // 10 MB limit for the entire request
	if err != nil {
		http.Error(w, "Error parsing form", http.StatusBadRequest)
		logger.Println(err)
		return
	}

	// Extract JSON data from the form
	var jsonRequest TranslateDocumentRequest
	jsonRequest.SourceLanguage = r.FormValue("source_language")
	jsonRequest.TargetLanguage = r.FormValue("target_language")
	jsonRequest.CustomPrompt = r.FormValue("custom_prompt")
	jsonRequest.Model = r.FormValue("model")

	// Access other form values as needed
	sourceLanguage := jsonRequest.SourceLanguage
	targetLanguage := jsonRequest.TargetLanguage
	customPrompt := jsonRequest.CustomPrompt
	model := jsonRequest.Model

	// Access the file from the form data
	file, _, err := r.FormFile("file")
	if err != nil {
		http.Error(w, "Error retrieving file", http.StatusBadRequest)
		logger.Println(err)
		return
	}
	defer file.Close()

	// Create a copy of the file
	tempFile, err := os.Create("temp.docx")
	if err != nil {
		http.Error(w, "Error processing file", http.StatusInternalServerError)
		logger.Println(err)
		return
	}
	// Delete the copy of the file when the function returns
	defer os.Remove("temp.docx")

	// Copy the file to the temp file
	_, err = io.Copy(tempFile, file)
	if err != nil {
		http.Error(w, "Error processing file", http.StatusInternalServerError)
		logger.Println(err)
		return
	}

	// --------------------------
	// Translation logic
	// --------------------------

	// Start the timer
	start := time.Now()

	// Log the start of the translation
	logger.Println("--------BEGIN TRANSLATION--------")

	// Log the source and target languages
	logger.Println("Source language:", sourceLanguage)
	logger.Println("Target language:", targetLanguage)
	if customPrompt != "" {
		logger.Println("Custom prompt:", customPrompt)
	}
	if model != "" {
		logger.Println("Model:", model)
	}

	// Read the file
	text := utils.ReadFile("temp.docx")

	// Get an array of sentences from the file
	sentences := utils.GetSentences(text)

	// Translate the file paragraph by paragraph
	for i, sentence := range sentences {
		// Log the paragraph number
		logger.Println("Sentence", i+1)

		// Translate the paragraph
		translation, err := utils.Translate(sentence, sourceLanguage, targetLanguage, customPrompt, model)
		if err != nil {
			http.Error(w, "Error translating", http.StatusInternalServerError)
			logger.Println(err)
			logger.Println("---------END TRANSLATION---------")
			return
		}

		// Append the translated paragraph to the output file
		utils.WriteMarkdown(translation, "output.md")
	}

	// Convert the output file to a .docx file
	err = utils.MarkdownToDocx("output.md")

	// Log that the translation was successful
	logger.Println("Translation successful")

	// Log the time elapsed
	elapsed := time.Since(start)
	logger.Printf("Time elapsed: %s", elapsed)

	// Relative path to the translated .docx file
	translatedFilePath := "output.docx"

	// Get the absolute path
	absTranslatedFilePath, err := filepath.Abs(translatedFilePath)
	if err != nil {
		http.Error(w, "Error getting absolute path", http.StatusInternalServerError)
		logger.Println(err)
		logger.Println("---------END TRANSLATION---------")
		return
	}

	// Open the file
	f, err := os.Open(absTranslatedFilePath)
	if err != nil {
		http.Error(w, "Error opening translated file", http.StatusInternalServerError)
		logger.Println(err)
		logger.Println("---------END TRANSLATION---------")
		return
	}
	defer f.Close()

	// Exit message
	logger.Println("--------END TRANSLATION--------")

	// ---------------------------------------
	// Serve the file via a download link
	// Only serve from the /downloads directory
	// ---------------------------------------

	// Create the downloads directory if it doesn't exist
	if _, err := os.Stat("downloads"); os.IsNotExist(err) {
		os.Mkdir("downloads", 0755)
	}

	// Create a cryptographically secure random string for the filename
	randStr, _ := randomString(LENGTH)
	name := fmt.Sprintf("%s_translation.docx", randStr)

	// Relative path to the file
	path := fmt.Sprintf("downloads/%s", name)

	// Create a copy of the file
	outputFile, err := os.Create(path)
	if err != nil {
		http.Error(w, "Error processing file", http.StatusInternalServerError)
		logger.Println(err)
		return
	}

	// Copy the file to the temp file
	_, err = io.Copy(outputFile, f)
	if err != nil {
		http.Error(w, "Error processing file", http.StatusInternalServerError)
		logger.Println(err)
		return
	}

	// Set the url to the download link
	url := fmt.Sprintf("%s%s/download?filename=%s", BASE_URL, PORT, name)

	// Send the download link to the client
	w.Write([]byte(url))

	// Delete the output file when the function returns
	defer os.Remove("output.md")
	defer os.Remove("output.docx")

	return
}

func downloadHandler(w http.ResponseWriter, r *http.Request) {
	// Create an ELF compliant logger
	// Log the time, date, and file name
	logger := log.New(os.Stdout, "INFO: ", log.Ldate|log.Ltime|log.Lshortfile)

	// Get the filename from the query string
	filename := r.URL.Query().Get("filename")

	// Relative path to the file
	relativePath := "downloads/" + filename

	// Get the absolute path
	absFilePath, err := filepath.Abs(relativePath)
	if err != nil {
		http.Error(w, "Error getting absolute path", http.StatusInternalServerError)
		logger.Println(err)
		return
	}

	// Open the file
	f, err := os.Open(absFilePath)
	if err != nil {
		http.Error(w, "Error opening file", http.StatusInternalServerError)
		logger.Println(err)
		return
	}
	defer f.Close()

	// Read the file into a byte array
	fileBytes, err := io.ReadAll(f)
	if err != nil {
		http.Error(w, "Error reading file", http.StatusInternalServerError)
		logger.Println(err)
		return
	}

	// Delete the file when the function returns
	defer os.Remove(absFilePath)

	// Set the content type header
	w.Header().Set("Content-Type", "application/octet-stream")

	// Set the content disposition header
	w.Header().Set("Content-Disposition", "attachment; filename="+filename)

	// Write the file to the response writer
	w.Write(fileBytes)

	return
}

func randomString(n int) (string, error) {
	ret := make([]byte, n)
	for i := 0; i < n; i++ {
		num, err := rand.Int(rand.Reader, big.NewInt(int64(len(CHARS))))
		if err != nil {
			return "", err
		}
		ret[i] = CHARS[num.Int64()]
	}

	return string(ret), nil
}
