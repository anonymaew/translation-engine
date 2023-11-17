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

type TranslateDocumentRequest struct {
	SourceLanguage string `json:"source_language"`
	TargetLanguage string `json:"target_language"`
}

func main() {
	// Initialize the server
	http.HandleFunc("/translate", translateDocumentHandler)
	http.ListenAndServe(":8080", nil)

	// Exit the program
	os.Exit(0)

}

func translateDocumentHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Parse the form data including the file and the JSON data
	err := r.ParseMultipartForm(10 << 20) // 10 MB limit for the entire request
	if err != nil {
		http.Error(w, "Error parsing form", http.StatusBadRequest)
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
		return
	}
	defer file.Close()

	// Create a copy of the file
	tempFile, err := os.Create("temp.docx")
	if err != nil {
		http.Error(w, "Error processing file", http.StatusInternalServerError)
		return
	}

	defer os.Remove("temp.docx")
	_, err = io.Copy(tempFile, file)
	if err != nil {
		http.Error(w, "Error processing file", http.StatusInternalServerError)
		return
	}


	// --------------------------
	// Translation logic
	// --------------------------

	// Create a logger
	logger := log.New(os.Stdout, "INFO: ", log.Ldate|log.Ltime|log.Lshortfile)

	// Start the timer
	start := time.Now()

	// Read the file
	outfile := utils.ReadMarkdown("temp.docx")

	// Get an array of paragraphs from the file
	paragraphs := utils.GetParagraphs(outfile)

	// Translate the file paragraph by paragraph
	for i, paragraph := range paragraphs {
		// Log the paragraph number
		logger.Printf("Paragraph %d", i+1)

		// Translate the paragraph
		translation, err := utils.Translate(paragraph, sourceLanguage, targetLanguage)
		if err != nil {
			logger.Fatal(err)
		}

		// Append the translated paragraph to the output file
		err = utils.WriteMarkdown("output.md", translation + "\n\n")
		if err != nil {
			logger.Fatal(err)
		}

		// Convert the output file to a .docx file
		err = utils.MarkdownToDocx("output.md")

		// Log that the translation was successful
		logger.Println("Translation successful took", time.Since(start))

		// Example: Relative path to the translated .docx file
		translatedFilePath := "./output.docx"

		// Get the absolute path
		absTranslatedFilePath, err := filepath.Abs(translatedFilePath)
		if err != nil {
			http.Error(w, "Error getting absolute path", http.StatusInternalServerError)
			return
		}

		// Open the file
		file, err := os.Open(absTranslatedFilePath)
		if err != nil {
			http.Error(w, "Error opening translated file", http.StatusInternalServerError)
			return
		}
		defer file.Close()

		// Set the Content-Disposition header to trigger a download
		w.Header().Set("Content-Disposition", "attachment; filename=translated_file.docx")

		// Set the Content-Type header for a .docx file
		w.Header().Set("Content-Type", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

		// Serve the file content
		http.ServeContent(w, r, "translated_file.docx", time.Now(), file)
	}
}
