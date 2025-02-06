from typing import List
import requests
from hashlib import sha256
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET  # NOQA

from logger import Logger

NYT_RSS_FEED_URL = "https://rss.nytimes.com/services/xml/rss/nyt/Space.xml"
logging = Logger.setup_logger(__name__)

# Example pubDate format: "Fri, 22 Sep 2023 09:13:12 +0000"
date_format = "%a, %d %b %Y %H:%M:%S %z"

# Define the allowed date range (last 2 days)
MAX_AGE_DAYS = 2  
cutoff_date = datetime.now().date() - timedelta(days=MAX_AGE_DAYS)

def pull_from_nyt(already_pushed: List[str]) -> List[str]:
    space_queue = []
    try:
        logging.info(f"Fetching feed from {NYT_RSS_FEED_URL}")

        response = requests.get(NYT_RSS_FEED_URL)
        response.raise_for_status()
        logging.info("Successfully retrieved NewYork Times Space feed.")

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
            link_hash = sha256(item_guid.encode()).hexdigest()
            created_at = datetime.strptime(pubdate_elem.text, date_format)

            if created_at.date() < cutoff_date:
                continue

            # Skip if this GUID is already seen
            if link_hash in already_pushed:
                logging.info(f"Skipping already processed item with GUID: {link_hash}")
                continue

            # Add new item
            space_queue.append(title)
            already_pushed.append(link_hash)

        logging.info(f"Number of new posts added to the queue: {len(space_queue)}")
        return space_queue

    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error: {req_err}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

    return space_queue
