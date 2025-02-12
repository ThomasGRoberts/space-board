from typing import List
import requests
from hashlib import md5
from datetime import datetime, timezone
import xml.etree.ElementTree as ET  # NOQA

from logger import Logger


# URL of the SpaceNews RSS feed
SOURCE = 'spacenews'
RSS_FEED_URL = "https://spacenews.com/feed/"

logging = Logger.setup_logger(__name__)

# Sat, 21 Sep 2024 06:32:38 +0000
date_format = "%a, %d %b %Y %H:%M:%S %z"


def pull_from_spacenews(already_pushed: List[int]) -> List[str]:
    res = []
    try:

        logging.info(f"Fetching SpaceNews RSS feed from {RSS_FEED_URL}")

        # Make the request to the RSS feed
        response = requests.get(RSS_FEED_URL)
        response.raise_for_status()

        logging.info("Successfully retrieved RSS feed.")

        # Parse the XML content
        root = ET.fromstring(response.content)
        items = root.findall('.//item')

        # Process each item in the feed
        for item in items:
            message = item.find('./title').text
            link = item.find('link').text

            created_at = datetime.strptime(item.find('./pubDate').text, date_format)
            if created_at.date() != datetime.now(created_at.tzinfo).date():
                continue

            id = md5((SOURCE + message).encode()).hexdigest()

            if id in already_pushed:
                logging.info(f"Skipping already processed item with id: {id}")
                continue

            # Add new item
            res.append({
                "id": id,
                "source": SOURCE,
                "text": message,
                "source_link": link,
                "shown": False,
                "type": "news",
                "fetched_datetime": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            })
            already_pushed.append(id)

        logging.info(f"Number of new posts added to the queue: {len(res)}")
        return res

    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error: {req_err}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

    return res
