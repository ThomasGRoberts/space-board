import requests
import json
import os

# Retrieve environment variables
SANITY_API_URL = os.getenv('SANITY_API_URL')
VESTABOARD_API_KEY = os.getenv('VESTABOARD_API_KEY')

# Fetch all launches from Sanity API
def fetch_all_launches():
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.get(SANITY_API_URL, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data['result']
    else:
        print("Failed to fetch data from Sanity API")
        print("Status Code:", response.status_code)
        print("Response Text:", response.text)
        return []

# Get the most recent launch from the list
def get_most_recent_launch(launches):
    if not launches:
        return None
    # Sort launches by a date field if available (assuming '_createdAt' for example)
    launches.sort(key=lambda x: x['_createdAt'], reverse=True)
    return launches[0]

# Format the launch description
def format_launch_description(launch):
    description = launch.get('description', 'No description available')
    return f"{launch['name']}: {description}"

# Create Vestaboard message layout
def create_vestaboard_message(message):
    character_map = {
        'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9, 'J': 10, 'K': 11, 'L': 12, 'M': 13,
        'N': 14, 'O': 15, 'P': 16, 'Q': 17, 'R': 18, 'S': 19, 'T': 20, 'U': 21, 'V': 22, 'W': 23, 'X': 24, 'Y': 25,
        'Z': 26, '1': 27, '2': 28, '3': 29, '4': 30, '5': 31, '6': 32, '7': 33, '8': 34, '9': 35, '0': 36, '!': 37,
        '@': 38, '#': 39, '$': 40, '(': 41, ')': 42, '-': 44, '+': 46, '&': 47, '=': 48, ';': 49, ':': 50, "'": 52,
        '"': 53, '%': 54, ',': 55, '.': 56, '/': 59, '?': 60, '°': 62, ' ': 0
    }
    # Initialize an empty layout with blanks
    layout = [[0]*22 for _ in range(6)]
    # Flatten the message and map characters
    flat_message = list(message.upper())
    char_codes = [character_map.get(char, 0) for char in flat_message]
    
    # Fill the layout with the character codes
    idx = 0
    for row in range(6):
        for col in range(22):
            if idx < len(char_codes):
                layout[row][col] = char_codes[idx]
                idx += 1
    
    return layout

# Send message to Vestaboard
def send_to_vestaboard(message_layout):
    url = 'https://rw.vestaboard.com/'
    headers = {
        'X-Vestaboard-Read-Write-Key': VESTABOARD_API_KEY,
        'Content-Type': 'application/json'
    }
    data = json.dumps(message_layout)  # Directly dump the layout without wrapping it in a dictionary
    print("Message Layout:", data)  # Log the message layout for debugging
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        print("Message sent to Vestaboard successfully!")
    else:
        print("Failed to send message to Vestaboard")
        print("Status Code:", response.status_code)
        print("Response Headers:", response.headers)
        print("Response Text:", response.text)

# Main script execution
if not SANITY_API_URL or not VESTABOARD_API_KEY:
    print("Environment variables SANITY_API_URL and VESTABOARD_API_KEY must be set.")
else:
    launches = fetch_all_launches()
    most_recent_launch = get_most_recent_launch(launches)
    if most_recent_launch:
        description = format_launch_description(most_recent_launch)
        message_layout = create_vestaboard_message(description)
        send_to_vestaboard(message_layout)
    else:
        print("No launches found.")
