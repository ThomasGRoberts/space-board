import json
from datetime import datetime, timedelta, timezone
import hashlib
from utils import get_time_remaining
import random 
from dotenv import load_dotenv

from aidy import pull_from_aidy
from logger import Logger
from space import pull_from_space
from spacenews import pull_from_spacenews
from supercluster import pull_from_supercluster
from nyt import pull_from_nyt
from vestaboard import push_to_vestaboard

# Set up logging
logging = Logger.setup_logger(__name__)

load_dotenv()
DB_PATH = 'data.json'

CURRENT_DATE = datetime.now().strftime('%Y-%m-%d')
YESTERDAY_DATE = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

def load_data():
    logging.info('Loading data')
    return json.load(open(DB_PATH))

def save_data(db):
    logging.info('Saving data')
    with open(DB_PATH, 'w') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)
    
def migrate_to_v2(db):
    logging.info("Migrating data to version 2")
    if db.get("version") == "2":
        return db

    new_db = {
        "version": "2",
        "last_run_datetime": datetime.now(timezone.utc).isoformat(),
        "data": [],
        "trigger_count": 0
    }

    for item in db.get("old_updates", []):
        source = item.get("source", "").strip()
        text = item.get("data", "").strip()
        date = item.get("date", "").strip()
        record = {
            "id": hashlib.md5((source + text).encode()).hexdigest(),
            "source": source,
            "text": text,
            "shown": True,
            "type": "news",
            "fetched_datetime": f"{date}T00:00:00.000Z" if date else ""
        }
        new_db["data"].append(record)
    return new_db

def update_data(db):
    logging.info('Updating data')
    current_date = datetime.now(timezone.utc).date()
    last_run_str = db.get("last_run_datetime")
    if last_run_str:
        last_run_date = datetime.fromisoformat(last_run_str.replace("Z", "+00:00")).date()
        if last_run_date == current_date:
            return db  # Already updated today

    sorted_items = sorted(
        db.get("data", []),
        key=lambda item: datetime.fromisoformat(item["fetched_datetime"].replace("Z", "+00:00")),
        reverse=True
    )

    new_items = []
    older_items_seen = 0
    for item in sorted_items:
        new_items.append(item)
        fetched_date = datetime.fromisoformat(item["fetched_datetime"].replace("Z", "+00:00")).date()
        if fetched_date != current_date:
            older_items_seen += 1
        if older_items_seen >= 11:
            break

    db["data"] = new_items
    db["last_run_datetime"] = datetime.now(timezone.utc).isoformat()
    return db

SOURCES = {
    # "space": pull_from_space,
    # "aidy": pull_from_aidy,
    "supercluster": pull_from_supercluster,
    # "spacenews": pull_from_spacenews,
    # "nyt": pull_from_nyt
}

def get_unseen_item_for_source(DB, source_name):
    for item in DB.get("data", []):
        if item.get("source") == source_name and not item.get("shown", False):
            return item
    return None

def fetch_new_items(source, already_seen):
    return SOURCES[source](already_seen)

def get_current_item(db):
    current_item_id = db.get("current_item_id")
    if not current_item_id:
        return None
    return next((item for item in db.get("data", []) if item.get("id") == current_item_id), None)


def execute(db):
    logging.info("Executing steps to fetch new data and push to vestaboard.")

    current_item = get_current_item(db)
    db["trigger_count"] = db.get("trigger_count", 0) + 1

    if db["trigger_count"] >= 15:
        db["trigger_count"] = 0
    elif current_item and current_item['type'] == 'launch':
        current_item['time_remaining'] = get_time_remaining(current_item['target_datetime'])
        push_to_vestaboard(current_item)
        return

    for source_name, _ in SOURCES.items():
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

    if db.get("data"):
        item = random.choice(db["data"])
        logging.info(f"Pushing random item: {item.get('text', '')}")
        push_to_vestaboard(item)
        db["current_item_id"] = item["id"]

def main():
    DB = load_data()
    DB = migrate_to_v2(DB)
    DB = update_data(DB)
    
    execute(DB)
    
    DB = save_data(DB)

if __name__ == '__main__':
    main()