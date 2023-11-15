import requests
import sys

# The following function makes a request to the model API
# The function accepts a string of Chinese text
# as well as a string of context in either English or Chinese
# The context is used to improve the translation
# context is optional and defaults to None
# The function returns a string of English text
def translate(port, text, context=None):
    # Check if the text is valid
    if not is_valid(text):
        # Log the error
        print("Invalid text: " + text)
        # Exit the program
        sys.exit(1)

    if context is not None:
        # The URL for the model API
        url = "http://localhost:" + str(port) + "/translate"

        # The data to be sent to the model API
        data = {"text": text, "context": context}
    else:
        # The URL for the model API
        url = "http://localhost:" + str(port) + "/translate"

        # The data to be sent to the model API
        data = {"text": text}

    # Make a request to the model API
    response = requests.post(url, data=data)

    # Return the English translation
    return response.text

# The following function accepts a string of Chinese text
# It ensures that the text is valid UTF-8
# The function returns a boolean
def is_valid(text):
    try:
        text.encode("utf-8")
        return True
    except:
        return False

