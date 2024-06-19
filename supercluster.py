import os
import requests
import json

# Function to create a message layout for Vestaboard
def create_vestaboard_message(message):
    char_to_code = {
        '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
        'A': 10, 'B': 11, 'C': 12, 'D': 13, 'E': 14, 'F': 15, 'G': 16, 'H': 17, 'I': 18, 'J': 19,
        'K': 20, 'L': 21, 'M': 22, 'N': 23, 'O': 24, 'P': 25, 'Q': 26, 'R': 27, 'S': 28, 'T': 29,
        'U': 30, 'V': 31, 'W': 32, 'X': 33, 'Y': 34, 'Z': 35, ' ': 36, '.': 37, ',': 38, '!': 39,
        '?': 40, "'": 41, '"': 42, '&': 43, '@': 44, '#': 45, '$': 46, '%': 47, '^': 48, '*': 49,
        '(': 50, ')': 51, '-': 52, '_': 53, '+': 54, '=': 55, '/': 56, '\\': 57, '<': 58, '>': 59,
        '|': 60, '[': 61, ']': 62, '{': 63, '}': 64, ':': 65, ';': 66
    }

    # Maximum number of characters that can be displayed on the Vestaboard
    max_chars = 42

    # Truncate message if it exceeds maximum characters
    message = message[:max_chars]

    # Initialize layout for message
    layout = [0] * max_chars

    # Convert characters in message to Vestaboard codes
    for i, char in enumerate(message):
        layout[i] = char_to_code.get(char, 0)

    return layout

# Fetch data from the SuperCluster API
def fetch_data():
    url = "https://api.supercluster.com"
    query = {"query":"*[_type==\"launch\"]"}

    try:
        response = requests.request("POST", url, json=query)
        data = response.json()
        print("Successfully fetched data from SuperCluster API")
        print("API Response Snippet:", json.dumps(data)[:100])  # Print a snippet of the response
        return data
    except Exception as e:
        print("Failed to fetch data from SuperCluster API:", e)
        return None

# Main function
def main():
    # Fetch data from the SuperCluster API
    data = fetch_data()

    if data:
        # Extract message from API response
        description = data.get("result", [])[0].get("description", "")

        # Print the retrieved message
        print("SuperCluster Message:", description)

        # Create message layout for Vestaboard
        message_layout = create_vestaboard_message(description)

        # Print the message layout
        print("Vestaboard Message Layout:", message_layout)

        # Attempt to update the Vestaboard (TODO: Implement Vestaboard update logic)

# Entry point of the script
if __name__ == "__main__":
    main()
