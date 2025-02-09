from typing import List
import requests
import os
from datetime import datetime, timezone
from hashlib import md5
from logger import Logger
from dotenv import load_dotenv
from utils import get_time_remaining

load_dotenv()

# Set up logging
logging = Logger.setup_logger(__name__)

# Retrieve environment variables
SOURCE = 'supercluster'
SANITY_API_URL = os.getenv('SANITY_API_URL')
TODAY_DATE = datetime.utcnow().strftime("%Y-%m-%d")


def pull_from_supercluster(already_pushed: List[str]):
    logging.info("Starting pull from Supercluster")
    query = f'\n*[\n  _type == "launch"\n  && !(_id in path("drafts.**"))\n  && launchInfo.launchDate.utc match "2025-03*"\n] | order(launchInfo.launchDate.utc desc) {{\n  ...\n}}\n'
    # query = f'\n*[\n  _type == "launch"\n  && !(_id in path("drafts.**"))\n  && launchInfo.launchDate.utc match "{TODAY_DATE}*"\n] | order(launchInfo.launchDate.utc desc) {{\n  ...\n}}\n'
    # query = f'\n*[\n  _type == "launch"\n  && !(_id in path("drafts.**"))\n  && launchInfo.launchDate.utc match "2024*"\n] | order(launchInfo.launchDate.utc desc) {{\n  ...\n}}\n'
    params = {'query': query}
    res = []

    try:
        logging.info(f"Sending request to SANITY API at {SANITY_API_URL} with params: {params}")
        response = requests.get(SANITY_API_URL, params=params)
        response.raise_for_status()

        logging.info("Successfully received response from SANITY API")
        response_json = response.json()

        for launch in response_json["result"]:
            message = launch["launchInfo"]["launchMiniDescription"]
            id = md5((SOURCE + message).encode()).hexdigest()

            if id in already_pushed:
                logging.info(f"Skipping already processed item with id: {id}")
                continue

            # Add new item
            res.append({
                "id": id,
                "source": SOURCE,
                "text": message,
                "shown": False,
                "type": "launch",
                "target_datetime": launch["launchInfo"]["launchDate"]["utc"], 
                "time_remaining": get_time_remaining(launch["launchInfo"]["launchDate"]["utc"]),
                "fetched_datetime": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            })
            already_pushed.append(id)

        logging.info(f"Number of launches added to the queue: {len(res)}")
        return res

    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error: {req_err}")
        return res
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return res
