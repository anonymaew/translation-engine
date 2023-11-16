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
	"log"
	"os"
	"strings"

	"translation-engine/src/gollama/utils"
)

func main() {
	var translated_paragraphs []string
	
	// Create a logger
	logger := log.New(os.Stdout, "INFO: ", log.Ldate|log.Ltime|log.Lshortfile)

	// Check that an argument was passed
	if len(os.Args) < 2 {
		logger.Fatal("No file name provided")
	}

	// Get file name from args
	fileName := os.Args[1]

	// Check that the file exists
	if !utils.FileExists(fileName) {
		logger.Fatal("File does not exist")
	}

	// Read the file
	file := utils.ReadMarkdown(fileName)

	// Get an array of paragraphs from the file
	paragraphs := utils.GetParagraphs(file)

	// Translate the file paragraph by paragraph
	for i, paragraph := range paragraphs {
		// Log the paragraph number
		logger.Printf("Paragraph %d", i+1)

		// Log the paragraph
		logger.Println(paragraph)

		// Translate the paragraph
		translation, err := utils.Translate(paragraph)
		if err != nil {
			logger.Fatal(err)
		}

		// Append the translated paragraph to the output file
		err = utils.WriteMarkdown("output.md", translation)
		if err != nil {
			logger.Fatal(err)
		}

	}

	// Log that the translation was successful
	logger.Println("Translation complete")

	// Exit the program
	os.Exit(0)

}
