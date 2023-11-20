package main

// The main file for the program
// Author: Korben Tompkin

// The following program is middleware for a translation engine
// Powered by Large Language Models installed with ollama
// The engine accepts Chinese text and translates it to Academic English
// The engine runs inside of a docker container
// The model API is exposed on port 11434
// The engine accepts text via a POST request to /api/generate
// The engine returns a JSON stream of the translated text

import (
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"translation-engine/src/gollama/utils"
)

const (
	// The port that the server will run on
	PORT = ":8080"
)

type TranslateDocumentRequest struct {
	SourceLanguage string `json:"source_language"`
	TargetLanguage string `json:"target_language"`
}

func main() {
	// Initialize the server
	http.HandleFunc("/translate", translateDocumentHandler)
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

	// Access other form values as needed
	sourceLanguage := jsonRequest.SourceLanguage
	targetLanguage := jsonRequest.TargetLanguage

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

	// Read the file
	text := utils.ReadFile("temp.docx")

	// Get an array of paragraphs from the file
	paragraphs := utils.GetParagraphs(text)

	// Translate the file paragraph by paragraph
	for i, paragraph := range paragraphs {
		// Log the paragraph number
		logger.Println("Paragraph", i+1)

		// Translate the paragraph
		translation, err := utils.Translate(paragraph, sourceLanguage, targetLanguage)
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

	// Set the Content-Disposition header to trigger a download
	w.Header().Set("Content-Disposition", "attachment; filename=translated_file.docx")

	// Set the Content-Type header for a .docx file
	w.Header().Set("Content-Type", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

	// Serve the file content
	http.ServeContent(w, r, translatedFilePath, time.Now(), f)

	// Delete the output file when the function returns
	defer os.Remove("output.md")
	defer os.Remove("output.docx")

	return
}
