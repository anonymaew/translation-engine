package utils

// Suite of functions for working with documents in the translation engine
// Author: Korben Tompkin

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// Check if file exists
func FileExists(filename string) bool {
	if _, err := os.Stat(filename); os.IsNotExist(err) {
		return false
	}
	return true
}

// Check if file is a markdown file
func toMarkdown(filename string) error {
	if strings.HasSuffix(filename, ".md") {
		return nil
	}
	err := callPandoc(filename)
	return err
}

// Call pandoc to convert to markdown
func callPandoc(filename string) error {
	// Get the file extension
	ext := filepath.Ext(filename)
	// Get the filename without the extension
	name := strings.TrimSuffix(filename, ext)
	// Make the pandoc call
	cmd := exec.Command("pandoc", "-f", ext[1:], "-t", "markdown", filename, "-o", name+".md")
	err := cmd.Run()
	if err != nil {
		return err
	}
	return nil
}

// Read the markdown file
func ReadMarkdown(filename string) string {
	err := toMarkdown(filename)
	// Read the file
	data, err := os.ReadFile(filename)
	if err != nil {
		fmt.Println(err)
	}
	// Return the file as a string
	return string(data)
}

// Write the markdown file
func WriteMarkdown(data string, filename string) error {
	// If the file doesn't exist, create it, or append to the file
	f, err := os.OpenFile("access.log", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	if _, err := f.Write([]byte("appended some data\n")); err != nil {
		return err
	}
	if err := f.Close(); err != nil {
		return err
	}
	return nil
}

// Split content into paragraphs
func GetParagraphs(content string) []string {
	// Split the content into paragraphs
	paragraphs := strings.Split(content, "\n\n")
	return paragraphs
}

// Converts markdown to docx using pandoc
func MarkdownToDocx(filename string) error {
	// Get the file extension
	ext := filepath.Ext(filename)
	// Get the filename without the extension
	name := strings.TrimSuffix(filename, ext)
	// Make the pandoc call
	cmd := exec.Command("pandoc", "-f", "markdown", "-t", "docx", filename, "-o", name+".docx")
	err := cmd.Run()
	if err != nil {
		return err
	}
	return nil
}
