from typing import List
import requests
from hashlib import md5
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET  # NOQA

from logger import Logger

SOURCE = 'breaking_defense'
RSS_FEED_URL = "https://breakingdefense.com/full-rss-feed/?v=2"
logging = Logger.setup_logger(__name__)

# Example pubDate format: "Fri, 22 Sep 2023 09:13:12 +0000"
date_format = "%a, %d %b %Y %H:%M:%S %z"

# Define the allowed date range (last 2 days)
MAX_AGE_DAYS = 2  
cutoff_date = datetime.now().date() - timedelta(days=MAX_AGE_DAYS)

def pull_from_breaking_defense(already_pushed: List[str]) -> List[str]:
    res = []
    try:
        logging.info(f"Fetching feed from {RSS_FEED_URL}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(RSS_FEED_URL, headers=headers)

        response.raise_for_status()
        logging.info("Successfully retrieved breaking defense feed.")

        root = ET.fromstring(response.content)
        items = root.findall('.//item')

        for item in items:
            title_elem = item.find('title')
            pubdate_elem = item.find('pubDate')
            categories = [cat.text.strip().lower() for cat in item.findall('category') if cat.text]

            # Check for missing required fields
            if title_elem is None or pubdate_elem is None or 'space' not in categories:
                continue

            message = title_elem.text
            link = item.find('link').text


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
