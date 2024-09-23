from typing import List
import requests
import os
from datetime import datetime

from logger import Logger
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging = Logger.setup_logger(__name__)

# Retrieve environment variables
SANITY_API_URL = os.getenv('SANITY_API_URL')
TODAY_DATE = datetime.utcnow().strftime("%Y-%m-%d")


def pull_from_supercluster(already_pushed: List[str]):
    logging.info("Starting pull from Supercluster")
    query = f'\n*[\n  _type == "launch"\n  && !(_id in path("drafts.**"))\n  && launchInfo.launchDate.utc match "{TODAY_DATE}*"\n] | order(launchInfo.launchDate.utc desc) {{\n  ...\n}}\n'
    # query = f'\n*[\n  _type == "launch"\n  && !(_id in path("drafts.**"))\n  && launchInfo.launchDate.utc match "2024*"\n] | order(launchInfo.launchDate.utc desc) {{\n  ...\n}}\n'
    params = {'query': query}
    supercluster_queue = []

    try:
        logging.info(f"Sending request to SANITY API at {SANITY_API_URL} with params: {params}")
        response = requests.get(SANITY_API_URL, params=params)
        response.raise_for_status()

        logging.info("Successfully received response from SANITY API")
        response_json = response.json()

        for launch in response_json["result"]:
            if launch["_id"] in already_pushed:
                logging.info(f"Skipping already pushed launch with ID: {launch['_id']}")
                continue
            logging.info(f"Adding launch with headline: {launch['headline']}")
            supercluster_queue.append(f"{launch['headline']}")
            already_pushed.append(launch["_id"])

        logging.info(f"Number of launches added to the queue: {len(supercluster_queue)}")
        return supercluster_queue

    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error: {req_err}")
        return supercluster_queue
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return supercluster_queue
