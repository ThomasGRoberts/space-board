import os
from datetime import datetime
from hashlib import sha256
from typing import List

from dotenv import load_dotenv
import requests

from logger import Logger

load_dotenv()

# Set up logging
logging = Logger.setup_logger(__name__)

AIDY_API_URL = os.environ.get('AIDY_API_URL') + "/api/topics/summarizer"
AIDY_TOPICS = os.environ.get('AIDY_TOPICS').split(",")


def pull_from_aidy(already_pushed: list[str]) -> List[str]:
    aidy_queue = []

    try:
        for topic in AIDY_TOPICS:
            logging.info(f"Requesting bills for topic: {topic}")
            # Make API request
            response = requests.get(f"{AIDY_API_URL}/{topic}")
            response.raise_for_status()  # Will raise HTTPError if the status code is 4xx, 5xx
            response = response.json()
            summary = response["current_summary"]
            created_id = sha256(response["current_summary"].encode()).hexdigest()
            if created_id in already_pushed:
                logging.info(f"Already pushed {created_id}")
                continue
            logging.info("Successfully retrieved response from AIDY API.")
            aidy_queue.append(summary)
            already_pushed.append(created_id)
        return aidy_queue

    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error: {req_err}")
    except Exception as e:

        logging.error(f"An error occurred: {str(e)}")
        # raise e

    return aidy_queue
