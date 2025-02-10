import os
import json
import logging
import requests
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

VESTABOARD_API_URL = os.getenv('VESTABOARD_API_URL')
headers = {
    'X-Vestaboard-Read-Write-Key': os.getenv('VESTABOARD_API_KEY')
}

CURRENT_DATE = datetime.now().strftime('%Y-%m-%d')

# Character mapping for Vestaboard
char_to_code = {
    ' ': 0, 'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9, 'J': 10, 'K': 11, 'L': 12, 'M': 13,
    'N': 14, 'O': 15, 'P': 16, 'Q': 17, 'R': 18, 'S': 19, 'T': 20, 'U': 21, 'V': 22, 'W': 23, 'X': 24, 'Y': 25, 'Z': 26,
    '1': 27, '2': 28, '3': 29, '4': 30, '5': 31, '6': 32, '7': 33, '8': 34, '9': 35, '0': 36, '!': 37, '@': 38, '#': 39,
    '$': 40, '(': 41, ')': 42, '-': 44, '+': 46, '&': 47, '=': 48, ';': 49, ':': 50, "'": 52, '"': 53, '%': 54, ',': 55,
    '.': 56, '/': 59, '?': 60, '°': 62, 'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8, 'i': 9, 'j': 10,
    'k': 11, 'l': 12, 'm': 13, 'n': 14, 'o': 15, 'p': 16, 'q': 17, 'r': 18, 's': 19, 't': 20, 'u': 21, 'v': 22, 'w': 23,
    'x': 24, 'y': 25, 'z': 26
}


def format_message_for_grid(content, line_lengths, max_lines=5):
    logging.info("Formatting message for grid.")
    words = content.split()
    lines = []
    current_line = ""
    line_idx = 0

    for word in words:
        if len(current_line) + len(word) + (1 if current_line else 0) > line_lengths[line_idx]:
            lines.append(current_line)
            current_line = word
            line_idx += 1

            if line_idx >= max_lines:
                lines[-1] = lines[-1][:line_lengths[line_idx - 1] - 3] + '...'  # add ellipsis if it exceeds max lines
                break
        else:
            if current_line:
                current_line += " " + word
            else:
                current_line = word

    if line_idx < max_lines:
        lines.append(current_line)

    return lines

def format_rest_message(message, color, time_remaining=''):
    logging.info("Formatting message with color.")
    content = " ".join(format_message_for_grid(message, line_lengths=[22, 22, 22, 22, 22, 20], max_lines=6))

    return {
        "components": [
            {
                "style": {
                    "justify": "center",
                    "align": "center",
                    "width": 22,
                    "height": 6
                },
                "template": f"{content}"
            },
            {
                "style": {
                    "width": 12,
                    "height": 1,
                    "absolutePosition": {
                        "x": 6,
                        "y": 5
                    },
                },
                "template": f"{time_remaining}"
            },
            {
                "style": {
                    "width": 1,
                    "height": 1,
                    "absolutePosition": {
                        "x": 21,
                        "y": 5
                    },
                },
                "template": f"{{{color}}}"
            }
        ]
    }


def create_vestaboard_message(title):
    logging.info("Creating Vestaboard message.")
    message_layout = [[0 for _ in range(22)] for _ in range(6)]

    words = title.split(' ')
    current_row = []
    current_line_length = 0
    temp_message_layout = []

    for word in words:
        word = word.replace("’", "'")
        word_length = len(word)

        if current_line_length + word_length <= 22:
            current_row.append(word)
            current_line_length += word_length + 1
        else:
            line = ' '.join(current_row)
            if len(line) > 22:
                line = line[:22]
            num_spaces = (22 - len(line)) // 2

            temp_row = [0] * 22
            start_index = num_spaces
            for i, char in enumerate(line):
                if start_index + i < 22:
                    temp_row[start_index + i] = char_to_code.get(char, 0)
            temp_message_layout.append(temp_row)

            current_row = [word]
            current_line_length = word_length + 1

    if current_row:
        line = ' '.join(current_row)
        if len(line) > 22:
            line = line[:22]
        num_spaces = (22 - len(line)) // 2
        temp_row = [0] * 22
        start_index = num_spaces
        for i, char in enumerate(line):
            if start_index + i < 22:
                temp_row[start_index + i] = char_to_code.get(char, 0)
        temp_message_layout.append(temp_row)

    num_rows = len(temp_message_layout)
    start_row = max(0, (6 - num_rows) // 2)

    for i in range(min(num_rows, 6)):
        message_layout[start_row + i] = temp_message_layout[i]

    message_layout[-1][-1] = 63

    return message_layout


def push_to_vestaboard(item):
    logging.info(f"Pushing message to Vestaboard from source: {item['source']}")
    try:
        if item["source"] == "aidy":
            vba_data = format_rest_message(message=item["text"], color=64)
        elif item["source"] == "supercluster":
            vba_data = format_rest_message(message=item["text"], color=65, time_remaining=item["time_remaining"])
        elif item["source"] == "spacenews":
            vba_data = format_rest_message(message=item["text"], color=63)
        elif item["source"] == "space":
            vba_data = format_rest_message(message=item["text"], color=67)
        elif item["source"] == "nyt":
            vba_data = format_rest_message(message=item["text"], color=69)
        elif item["source"] == "error":
            vba_data = format_rest_message(message=item["text"], color=68)

        logging.info(f"Formatted message for Vestaboard: {json.dumps(vba_data)}")

        layout_response = requests.post('https://vbml.vestaboard.com/compose', headers=headers, json=vba_data)
        # layout_response.raise_for_status()
        logging.info("Layout response received from Vestaboard.")

        vestaboard_response = requests.post('https://rw.vestaboard.com/', headers=headers, json=layout_response.json())
        # vestaboard_response.raise_for_status()
        logging.info(f"Message pushed to Vestaboard successfully: {vestaboard_response.text}")

        item["shown"] = True

    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error while pushing to Vestaboard: {req_err}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
