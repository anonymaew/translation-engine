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

	"translation-engine/src/gollama/utils"
)

func main() {
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

	// Translate the file
	translation, err := utils.Translate(file)
	if err != nil {
		logger.Fatal(err)
	}

	logger.Println(translation)

	// Write the translation to a file
	utils.WriteMarkdown(translation, "output.md")

	// Log that the translation was successful
	logger.Println("Translation complete")

	// Exit the program
	os.Exit(0)

}
