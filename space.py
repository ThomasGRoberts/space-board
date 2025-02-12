from typing import List
import requests
from hashlib import md5
from datetime import datetime, timezone
import xml.etree.ElementTree as ET  # NOQA

from logger import Logger

SOURCE = 'space'
SPACE_RSS_FEED_URL = "https://www.space.com/feeds/all"
logging = Logger.setup_logger(__name__)

# Example pubDate format: "Fri, 22 Sep 2023 09:13:12 +0000"
date_format = "%a, %d %b %Y %H:%M:%S %z"

def pull_from_space(already_pushed: List[str]) -> List[str]:
    res = []
    try:
        logging.info(f"Fetching feed from {SPACE_RSS_FEED_URL}")

        response = requests.get(SPACE_RSS_FEED_URL)
        response.raise_for_status()
        logging.info("Successfully retrieved space.com feed.")

        root = ET.fromstring(response.content)
        items = root.findall('.//item')

        for item in items:
            title_elem = item.find('title')
            pubdate_elem = item.find('pubDate')

            # Check for missing required fields
            if title_elem is None or pubdate_elem is None:
                continue

            message = title_elem.text
            link = item.find('link').text


            created_at = datetime.strptime(pubdate_elem.text, date_format)
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
