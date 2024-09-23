from typing import List
import requests
from datetime import datetime
import xml.etree.ElementTree as ET  # NOQA

from logger import Logger


# URL of the SpaceNews RSS feed
RSS_FEED_URL = "https://spacenews.com/feed/"

logging = Logger.setup_logger(__name__)

# Sat, 21 Sep 2024 06:32:38 +0000
date_format = "%a, %d %b %Y %H:%M:%S %z"


def pull_from_spacenews(already_pushed: List[int]) -> List[str]:
    spacenews_queue = []
    try:

        logging.info(f"Fetching SpaceNews RSS feed from {RSS_FEED_URL}")

        # Make the request to the RSS feed
        response = requests.get(RSS_FEED_URL)
        response.raise_for_status()

        logging.info("Successfully retrieved RSS feed.")

        # Parse the XML content
        root = ET.fromstring(response.content)
        spacenews_items = root.findall('.//item')

        namespaces = {'wp': 'com-wordpress:feed-additions:1'}

        # Process each item in the feed
        for spacenews_item in spacenews_items:
            title = spacenews_item.find('./title').text
            post_id = int(spacenews_item.find('./wp:post-id', namespaces).text)
            created_at = datetime.strptime(spacenews_item.find('./pubDate').text, date_format)
            if created_at.date() != datetime.now(created_at.tzinfo).date():
                continue
                # pass
            if post_id in already_pushed:
                logging.info(f"Skipping already processed post with ID: {post_id}")
                continue
            spacenews_queue.append(title)
            already_pushed.append(post_id)

        logging.info(f"Number of new posts added to the queue: {len(spacenews_queue)}")
        return spacenews_queue

    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error: {req_err}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

    return spacenews_queue
