import os
import re
import requests
from hashlib import md5
from logger import Logger
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

from utils import get_time_remaining

load_dotenv()
logging = Logger.setup_logger(__name__)

SOURCE = 'supercluster'
SANITY_API_URL = os.getenv('SANITY_API_URL')
SUPERCLUSTER_URL = "https://www.supercluster.com"

def wait_until_not_calculating(driver, css_selector, timeout=30):
    return WebDriverWait(driver, timeout).until(
        lambda d: "calculating" not in d.find_element(By.CSS_SELECTOR, css_selector).text.lower()
    )

def fetch_next_launch_details() -> Optional[Tuple[str, str]]:
    """Fetch the Supercluster page and extract the launch message from the header."""
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    service = Service(executable_path="/usr/lib/chromium-browser/chromedriver")
    driver = webdriver.Chrome(service=service, options=opts)

    try:
        driver.get(SUPERCLUSTER_URL)
        try:
            WebDriverWait(driver, 30).until(
                lambda d: "calculating" not in d.find_element(By.CSS_SELECTOR, "div.launch__next").text.lower()
            )
        except Exception as e:
            logging.warning("Waiting for header update timed out or encountered an error: %s", e)
        html = driver.page_source
    finally:
        driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    header_div = soup.find("div", class_="launch__next")
    if not header_div:
        logging.info("No header found on Supercluster.")
        return None
    url_elem = header_div.find("a")

    header_text = header_div.get_text(strip=True)
    link = f"{SUPERCLUSTER_URL}{url_elem['href']}"

    # Extract message: e.g., from "Next Launch:01D:00H:56M:42SChina Will Launch Demo Flight..."
    pattern = r"^Next Launch:\d+D:\d+H:\d+M:\d+S(.*)$"
    match = re.match(pattern, header_text)
    if not match:
        logging.info("Header text did not match expected pattern.", header_text)
        return None
    launch_message = match.group(1).strip()
    return launch_message, link    


def get_launch_item_for_message(message: str, link_from_homepage: str, already_pushed: List[str]) -> Optional[Dict]:
    """
    Call the Sanity API to retrieve launch data and return a launch item whose
    mini-description matches the provided message.
    """
    query = (
        '\n*[\n  _type == "launch"\n  && !(_id in path("drafts.**"))\n'
        '  && launchInfo.launchDate.utc match "2025*"\n] | order(launchInfo.launchDate.utc desc) { ... }\n'
    )
    try:
        response = requests.get(SANITY_API_URL, params={'query': query})
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        logging.error(f"API request error: {err}")
        return None

    data = response.json()
    for launch in data.get("result", []):
        mini_desc = launch["launchInfo"]["launchMiniDescription"].strip()
        slug = launch["slug"]["current"].strip()
        link = f"{SUPERCLUSTER_URL}/launches/{slug}"

        if message == mini_desc and link == link_from_homepage:
            item_id = md5((SOURCE + message).encode()).hexdigest()
            if item_id in already_pushed:
                logging.info(f"Skipping already processed item with id: {item_id}")
                return None
            launch_date = launch["launchInfo"]["launchDate"]["utc"]
            return {
                "id": item_id,
                "source": SOURCE,
                "text": message,
                "source_link": link,
                "shown": False,
                "type": "launch",
                "target_datetime": launch_date,
                "time_remaining": get_time_remaining(launch_date),
                "fetched_datetime": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            }
    logging.info("No matching launch found in API data.")
    return None

def pull_from_supercluster(already_pushed: List[str]) -> List[Dict]:
    """
    Pulls a launch item from Supercluster by first extracting the header message,
    then querying the API for a matching launch.
    """
    message, link = fetch_next_launch_details()
    if not message:
        logging.info("No header message extracted.")
        return []
    launch_item = get_launch_item_for_message(message, link, already_pushed)
    return [launch_item] if launch_item else []