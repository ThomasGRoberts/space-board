import random 
from logger import Logger
from dotenv import load_dotenv
from datetime import datetime, timedelta

from nyt import pull_from_nyt
from aidy import pull_from_aidy
from breaking_defense import pull_from_breaking_defense
from spacenews import pull_from_spacenews
from supercluster import pull_from_supercluster
from vestaboard import push_to_vestaboard

from utils import get_db, save_db, get_time_remaining, generate_report, get_sorted_sources, get_random_recent_item

# Set up logging
logging = Logger.setup_logger(__name__)

load_dotenv()

DB_PATH = 'data.json'
CURRENT_DATE = datetime.now().strftime('%Y-%m-%d')
YESTERDAY_DATE = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
MESSAGE_CHANGE_FREQUENCY = 7

SOURCES = {
    "supercluster": pull_from_supercluster,
    "spacenews": pull_from_spacenews,
    "nyt": pull_from_nyt,
    "aidy": pull_from_aidy,
    "breaking_defense": pull_from_breaking_defense,
}


def get_unseen_item_for_source(DB, source_name):
    '''Get and item that has not been shown on the board yet'''
    for item in DB.get("data", []):
        if item.get("source") == source_name and not item.get("shown", False):
            return item
    return None

def fetch_new_items(source, already_seen):
    '''Fetch new items from source'''
    return SOURCES[source](already_seen)

def get_current_item(db):
    '''Get the current item shown on the board'''
    current_item_id = db.get("current_item_id")
    if not current_item_id:
        return None
    return next((item for item in db.get("data", []) if item.get("id") == current_item_id), None)


def execute(db):
    logging.info("Executing steps to fetch new data and push to vestaboard.")

    current_item = get_current_item(db)
    db["trigger_count"] = db.get("trigger_count", 0) + 1

    if db["trigger_count"] >= MESSAGE_CHANGE_FREQUENCY:
        db["trigger_count"] = 0
    elif current_item and current_item['type'] == 'launch':
        current_item['time_remaining'] = get_time_remaining(current_item['target_datetime'])
        push_to_vestaboard(current_item)
        return
    elif current_item and current_item['type'] != 'launch':
        return

    sorted_sources = get_sorted_sources(db)

    for source_name in sorted_sources:
        logging.info(f"Finding new messages from {source_name}")
        item = get_unseen_item_for_source(db, source_name)
        if item:
            push_to_vestaboard(item)
            db["current_item_id"] = item["id"]
            return

        existing_ids = [itm["id"] for itm in db.get("data", []) if itm.get("source") == source_name]
        new_items = fetch_new_items(source_name, existing_ids)
        if not new_items:
            continue

        db["data"].extend(new_items)
        item = get_unseen_item_for_source(db, source_name)
        if item:
            push_to_vestaboard(item)
            db["current_item_id"] = item["id"]
            return
    
    for source in sorted_sources:
        logging.info(f"Finding old messages from {source}")
        item = get_random_recent_item(db, source)
        if not item:
            continue
        logging.info(f"Pushing random item: {item.get('text', '')}")
        push_to_vestaboard(item)
        db["current_item_id"] = item["id"]
        break

def main():
    db = get_db()
    execute(db)    
    generate_report(db)
    db = save_db(db)

if __name__ == '__main__':
    main()