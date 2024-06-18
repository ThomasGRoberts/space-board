import requests
import json
import os

# Environment variables (these should be set in your GitHub Secrets)
SANITY_API_URL = os.getenv('SANITY_API_URL')
VESTABOARD_API_KEY = os.getenv('VESTABOARD_API_KEY')

# Function to fetch all launch information from Sanity
def fetch_all_launches():
    response = requests.get(SANITY_API_URL)
    if response.status_code == 200:
        print("Successfully fetched data from Sanity API")
        print("API Response Snippet:", response.text[:200])  # Print a snippet of the API response for debugging
        return response.json()['result']
    else:
        print("Failed to fetch data from Sanity API")
        return []

# Function to identify the most recently created launch
def get_most_recent_launch(launches):
    if not launches:
        return None
    most_recent_launch = max(launches, key=lambda x: x['_createdAt'])
    return most_recent_launch

# Function to format the launch description for Vestaboard
def format_launch_description(launch):
    launch_info = launch.get('launchInfo', {})
    launch_description = launch_info.get('launchMiniDescription', 'No description available')
    return launch_description

# Function to create the Vestaboard message layout
def create_vestaboard_message(description):
    # Initialize the board with empty values
    message_layout = [[0 for _ in range(22)] for _ in range(6)]
    
    words = description.split(' ')
    current_row = []
    current_line_length = 0

    temp_message_layout = []

    for word in words:
        word_length = len(word)
        
        # If the word fits in the current line, add it
        if current_line_length + word_length <= 22:
            current_row.append(word)
            current_line_length += word_length + 1  # +1 for the space
        else:
            # Calculate the number of spaces needed to center-align the line
            line = ' '.join(current_row)
            num_spaces = (22 - len(line)) // 2

            # Place the current row on the temp board with centered alignment
            temp_row = [0] * 22
            start_index = num_spaces
            for i, char in enumerate(line):
                if start_index + i < 22:  # Ensure no overflow
                    temp_row[start_index + i] = char_to_code.get(char, 0)
            temp_message_layout.append(temp_row)

            # Start the new row with the current word
            current_row = [word]
            current_line_length = word_length + 1
    
    # Add any remaining words in the current row
    if current_row:
        line = ' '.join(current_row)
        num_spaces = (22 - len(line)) // 2
        temp_row = [0] * 22
        start_index = num_spaces
        for i, char in enumerate(line):
            if start_index + i < 22:
                temp_row[start_index + i] = char_to_code.get(char, 0)
        temp_message_layout.append(temp_row)

    # Determine the starting row based on the number of rows in temp_message_layout
    num_rows = len(temp_message_layout)
    start_row = 0

    if num_rows == 1 or num_rows == 2:
        start_row = 2
    elif num_rows == 3 or num_rows == 4:
        start_row = 1
    elif num_rows == 5 or num_rows == 6:
        start_row = 0

    # Copy temp_message_layout to message_layout starting from start_row
    for i in range(num_rows):
        message_layout[start_row + i] = temp_message_layout[i]

    # Add yellow tile in the bottom-right-hand corner (character code 65)
    message_layout[-1][-1] = 65

    return message_layout

# Function to send the message to Vestaboard
def send_to_vestaboard(message_layout):
    url = 'https://rw.vestaboard.com/'
    headers = {
        'X-Vestaboard-Read-Write-Key': VESTABOARD_API_KEY,
        'Content-Type': 'application/json'
    }
    data = json.dumps(message_layout)
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        print("Message sent to Vestaboard successfully!")
    else:
        print("Failed to send message to Vestaboard")
        print("Response:", response.text)

# Function to read the last message from the file
def read_last_message():
    try:
        with open('supercluster.txt', 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return None

# Function to write the current message to the file
def write_current_message(message):
    with open('supercluster.txt', 'w') as file:
        file.write(message)

# Main script execution
if not SANITY_API_URL or not VESTABOARD_API_KEY:
    print("Environment variables SANITY_API_URL and VESTABOARD_API_KEY must be set.")
else:
    launches = fetch_all_launches()
    most_recent_launch = get_most_recent_launch(launches)
    if most_recent_launch:
        description = format_launch_description(most_recent_launch)
        current_message = create_vestaboard_message(description)
        last_message = read_last_message()

        if current_message != last_message:
            send_to_vestaboard(current_message)
            write_current_message(current_message)
        else:
            print("SuperCluster message is the same as the last time.")
    else:
        print("No launches found.")
