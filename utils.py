import os
import json
from logger import Logger
from datetime import datetime, timezone

logging = Logger.setup_logger(__name__)

DB_PATH = 'data.json'


def get_db():
    default_db = {
        "version": "2",
        "last_run_datetime": datetime.now(timezone.utc).isoformat(),
        "trigger_count": 0,
        "current_item_id": "",
        "data": []
    }
    if not os.path.exists(DB_PATH):
        return default_db

    try:
        with open(DB_PATH, 'r') as f:
            db = json.load(f)
    except Exception:
        return default_db

    if db.get("version") != "2":
        return default_db
    
    db = cleanup_db(db)

    logging.info('Loaded data')

    return db


def remove_old_launches(db):
    """
    Remove any items in db['data'] that have a 'target_datetime' in the past.
    Returns the updated db.
    """
    now = datetime.now(timezone.utc)
    filtered_items = []
    for item in db.get("data", []):
        #temporary - to be removed
        if item["source"] == 'supercluster' and item["id"] == 'c5a8096acaf97aa5410b23f295e7ac2c':
            continue
        target = item.get("target_datetime")
        if target:
            try:
                target_dt = datetime.fromisoformat(target.replace("Z", "+00:00"))
            except Exception:
                # If parsing fails, retain the item.
                filtered_items.append(item)
                continue
            if target_dt < now:
                # Skip items with expired target_datetime.
                continue
        filtered_items.append(item)
    db["data"] = filtered_items
    return db


def cleanup_db(db):
    db = remove_old_launches(db)

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

    logging.info('Cleaned up data')

    return db


def save_db(db):
    with open(DB_PATH, 'w') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

    logging.info('Saved data')


def get_time_remaining(target_time: str) -> str:
    # Convert target_time string (ISO format) to a datetime object.
    target_dt = datetime.fromisoformat(target_time.replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    if target_dt < now:
        return ""  # Target time has passed.
    delta = target_dt - now
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{days}d {hours:02d}h {minutes:02d}m"
