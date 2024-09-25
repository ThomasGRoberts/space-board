import os
from datetime import datetime
from typing import List

from dotenv import load_dotenv
import requests

from logger import Logger

load_dotenv()

# Set up logging
logging = Logger.setup_logger(__name__)

AIDY_API_URL = os.environ.get('AIDY_API_URL') + "/search-bills"

params = {
    'query': 'Space Policy',
    'policies': '',
    'chambers': '',
    'doc_type': 'bill',
    'start_date': datetime.now().strftime('%Y-%m-%d'),
    # 'start_date': "2024-01-01",
}


def pull_from_aidy(already_pushed: list[int]) -> List[str]:
    aidy_queue = []
    try:

        logging.info(f"Requesting bills with params: {params}")

        # Make API request
        response = requests.get(AIDY_API_URL, params=params)
        response.raise_for_status()  # Will raise HTTPError if the status code is 4xx, 5xx
        response = response.json()
        print(response)
        logging.info("Successfully retrieved response from AIDY API.")

        space_bills = response['objects']
        for space_bill in space_bills:
            if space_bill['id'] in already_pushed:
                logging.info(f"Skipping already processed bill with ID: {space_bill['id']}")
                continue

            actions = space_bill['actions']

            actions.sort(key=lambda x: datetime.strptime(x['actionDate'], '%Y-%m-%d'), reverse=True)

            if actions[0]['actionCode'] is None:
                logging.info(f"Skipping bill {space_bill['id']} with no action code")
                already_pushed.append(space_bill['id'])
                continue

            message = f"{space_bill['bill_type']} {space_bill['bill_number']}{(' ' + actions[0]['actionCode'].split(' ')[0]) if actions[0]['actionCode'] else ''}: {space_bill['title']}"
            aidy_queue.append(message)
            already_pushed.append(space_bill['id'])
        logging.info(f"Number of new bills added to the queue: {len(aidy_queue)}")

        return aidy_queue

    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error: {req_err}")
    except Exception as e:

        logging.error(f"An error occurred: {str(e)}")
        # raise e

    return aidy_queue
