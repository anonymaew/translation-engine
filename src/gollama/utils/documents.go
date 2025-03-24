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
func toMarkdown(filename string) (string, error) {
	if strings.HasSuffix(filename, ".md") {
		return "", nil
	}
	name, err := callPandoc(filename)
	return name, err
}

// Call pandoc to convert to markdown
func callPandoc(filename string) (string, error) {
	// Get the file extension
	ext := filepath.Ext(filename)
	// Get the filename without the extension
	name := strings.TrimSuffix(filename, ext)
	// Make the pandoc call
	cmd := exec.Command("pandoc", "-f", ext[1:], "-t", "markdown", filename, "-o", name+".md")
	err := cmd.Run()
	if err != nil {
		return "", err
	}
	return name + ".md", nil
}

// Read the markdown file
func ReadFile(filename string) string {
	name, err := toMarkdown(filename)
	if err != nil {
		fmt.Println(err)
	}
	// Read the newly created markdown file
	data, err := os.ReadFile(name)
	if err != nil {
		fmt.Println(err)
	}
	// Return the file as a string
	return string(data)
}

// Write the markdown file
func WriteMarkdown(data string, filename string) error {
	// If the file doesn't exist, create it, or append to the file
	f, err := os.OpenFile(filename, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	// Write the data to the file
	if _, err := f.Write([]byte(data)); err != nil {
		return err
	}
	if err := f.Close(); err != nil {
		return err
	}
	return nil
}

// Split content into paragraphs
func GetSentences(content string) []string {
	// Split the content into sentences using the . and 。
	if strings.Contains(content, "。") {
		fmt.Println("Chinese")
		sentences := strings.Split(content, "。")
		return sentences
	} else {
		fmt.Println("English")
		sentences := strings.Split(content, ".")
		return sentences
	}
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
