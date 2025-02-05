from typing import List
import requests
from datetime import datetime
import xml.etree.ElementTree as ET  # NOQA

from logger import Logger

SPACECOM_RSS_FEED_URL = "https://www.space.com/feeds/all"
logging = Logger.setup_logger(__name__)

# Example pubDate format: "Fri, 22 Sep 2023 09:13:12 +0000"
date_format = "%a, %d %b %Y %H:%M:%S %z"

def pull_from_space(already_pushed: List[str]) -> List[str]:
    space_queue = []
    try:
        logging.info(f"Fetching feed from {SPACECOM_RSS_FEED_URL}")

        response = requests.get(SPACECOM_RSS_FEED_URL)
        response.raise_for_status()
        logging.info("Successfully retrieved space.com feed.")

        root = ET.fromstring(response.content)
        items = root.findall('.//item')

        for item in items:
            title_elem = item.find('title')
            guid_elem = item.find('guid')
            pubdate_elem = item.find('pubDate')

            # Check for missing required fields
            if title_elem is None or guid_elem is None or pubdate_elem is None:
                continue

            title = title_elem.text
            item_guid = guid_elem.text
            created_at = datetime.strptime(pubdate_elem.text, date_format)

            # Only take today's items
            if created_at.date() != datetime.now(created_at.tzinfo).date():
                continue

            # Skip if this GUID is already seen
            if item_guid in already_pushed:
                logging.info(f"Skipping already processed item with GUID: {item_guid}")
                continue

            # Add new item
            space_queue.append(title)
            already_pushed.append(item_guid)

        logging.info(f"Number of new posts added to the queue: {len(space_queue)}")
        return space_queue

    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error: {req_err}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

    return space_queue
