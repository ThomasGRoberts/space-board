import os
import requests
from hashlib import md5
from typing import List
from logger import Logger
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

# Set up logging
logging = Logger.setup_logger(__name__)

SOURCE = 'aidy'
AIDY_API_URL = os.environ.get('AIDY_API_URL') + "/api/topics/summarizer"
AIDY_TOPICS = os.environ.get('AIDY_TOPICS').split(",")

def pull_from_aidy(already_pushed: list[str]) -> List[str]:
    res = []

    try:
        for topic in AIDY_TOPICS:
            logging.info(f"Requesting bills for topic: {topic}")
            # Make API request
            response = requests.get(f"{AIDY_API_URL}/{topic}")
            response.raise_for_status()  # Will raise HTTPError if the status code is 4xx, 5xx
            response = response.json()
            message = response["current_summary"]

            id = md5((SOURCE + message).encode()).hexdigest()

            if id in already_pushed:
                logging.info(f"Skipping already processed item with id: {id}")
                continue

            # Add new item
            res.append({
                "id": id,
                "source": SOURCE,
                "text": message,
                "source_link": "Unavailable",
                "shown": False,
                "type": "news",
                "fetched_datetime": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            })
            already_pushed.append(id)

            logging.info("Successfully retrieved response from AIDY API.")

        return res

    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error: {req_err}")
    except Exception as e:

        logging.error(f"An error occurred: {str(e)}")
        # raise e

    return res
