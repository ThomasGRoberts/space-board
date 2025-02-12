import requests
from hashlib import md5
from typing import List
from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as ET  # NOQA

from logger import Logger

SOURCE = 'nyt'
NYT_RSS_FEED_URL = "https://rss.nytimes.com/services/xml/rss/nyt/Space.xml"

logging = Logger.setup_logger(__name__)

# Example pubDate format: "Fri, 22 Sep 2023 09:13:12 +0000"
date_format = "%a, %d %b %Y %H:%M:%S %z"

# Define the allowed date range (last 2 days)
MAX_AGE_DAYS = 2  
cutoff_date = datetime.now().date() - timedelta(days=MAX_AGE_DAYS)

def pull_from_nyt(already_pushed: List[str]) -> List[str]:
    res = []
    try:
        logging.info(f"Fetching feed from {NYT_RSS_FEED_URL}")

        response = requests.get(NYT_RSS_FEED_URL)
        response.raise_for_status()
        logging.info("Successfully retrieved NewYork Times Space feed.")

        root = ET.fromstring(response.content)
        items = root.findall('.//item')

        for item in items:
            title_elem = item.find('title')
            link_elem = item.find('link')
            pubdate_elem = item.find('pubDate')

            # Check for missing required fields
            if title_elem is None or pubdate_elem is None:
                continue

            message = title_elem.text
            link = link_elem.text

            created_at = datetime.strptime(pubdate_elem.text, date_format)
            if created_at.date() < cutoff_date:
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
