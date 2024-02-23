package utils

import (
	"bufio"
	"errors"
	"strconv"
	"strings"
)

// Options Object
type Options struct {
	Temperature float64 `json:"temperature"`
	Context     int     `json:"context"`
}

// Initialize the options object
func NewOptions() Options {
	return Options{
		Temperature: 0.8,
		Context:     1024,
	}
}

// Error for invalid options
var ErrInvalidOptions = errors.New("invalid options")

// Parse the string from the input options field
func ParseOptions(opts string) (Options, error) {
	// Create a new options object
	var options Options

	// Initialize the options object
	options = NewOptions()

	// Check if the options string is empty
	if opts == "" {
		return options, nil
	}

	// Create a new reader
	reader := strings.NewReader(opts)

	// Create a new scanner
	scanner := bufio.NewScanner(reader)

	// Scan the options string
	for scanner.Scan() {
		// Slice the string on commas
		slices := strings.Split(scanner.Text(), ",")

		// Iterate over the slices
		for _, slice := range slices {
			// Slice the string on colons
			parts := strings.Split(slice, ":")
			if len(parts) != 2 {
				return options, ErrInvalidOptions
			}

			// Check the key and set the value
			switch parts[0] {
			case "temperature":
				temperature, err := strconv.ParseFloat(parts[1], 64)
				if err != nil {
					return options, ErrInvalidOptions
				}
				options.Temperature = temperature
			case "context":
				context, err := strconv.Atoi(parts[1])
				if err != nil {
					return options, ErrInvalidOptions
				}
				options.Context = context
			}
		}
	}

	// Return the options object
	return options, nil
}

// Convert the options object to a string
func (o Options) String() string {
	return "temperature:" + strconv.FormatFloat(o.Temperature, 'f', -1, 64) + ", " + "context:" + strconv.Itoa(o.Context)
}
