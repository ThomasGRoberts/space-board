import os
import json
import random
from logger import Logger
from datetime import datetime, timezone, timedelta


logging = Logger.setup_logger(__name__)

DB_PATH = 'data.json'
NUM_OF_OLD_NEWS_TO_KEEP = 500

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
        if older_items_seen >= NUM_OF_OLD_NEWS_TO_KEEP:
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


def get_sorted_sources(db):
    """Returns a list of source names sorted by last shown time (oldest first)."""
    very_old_time = "2000-01-01T00:00:00.000000Z"
    all_sources = set(item["source"] for item in db.get("data", []))
    source_last_shown = {source: very_old_time for source in all_sources}

    for item in db.get("data", []):
        source = item["source"]
        for shown_time in item.get("shown_at", []):
            source_last_shown[source] = max(source_last_shown[source], shown_time)

    return sorted(source_last_shown, key=source_last_shown.get)

def generate_report(db):
    now = datetime.now(timezone.utc)
    one_day_ago = now - timedelta(days=1)
    two_days_ago = now - timedelta(days=2)
    
    # Extracting data
    data = db.get("data", [])
    
    # Preparing source frequency data
    source_stats = {}
    
    for item in data:
        source = item["source"]
        fetched_datetime = datetime.fromisoformat(item["fetched_datetime"].replace('Z', '+00:00'))
        shown_at = [datetime.fromisoformat(dt.replace('Z', '+00:00')) for dt in item.get("shown_at", [])]
        
        if source not in source_stats:
            source_stats[source] = {"fetched_1d": 0, "fetched_2d": 0, "shown_1d": 0, "shown_2d": 0}
        
        if fetched_datetime:
            if fetched_datetime >= one_day_ago:
                source_stats[source]["fetched_1d"] += 1
            if fetched_datetime >= two_days_ago:
                source_stats[source]["fetched_2d"] += 1
        
        for shown_time in shown_at:
            if shown_time >= one_day_ago:
                source_stats[source]["shown_1d"] += 1
            if shown_time >= two_days_ago:
                source_stats[source]["shown_2d"] += 1
    
    # Preparing shown order data
    shown_order = []
    for item in data:
        for shown_time in item.get("shown_at", []):
            shown_order.append((shown_time, item["text"], item["source"]))
    
    # Sorting shown order by time
    shown_order.sort()
    
    # Writing report.md
    with open("report.md", "w", encoding="utf-8") as file:
        file.write("# Source Frequency\n\n")
        file.write("| Source | Fetched (Last 1 Day) | Fetched (Last 2 Days) | Shown (Last 1 Day) | Shown (Last 2 Days) |\n")
        file.write("|--------|------------------|------------------|----------------|----------------|\n")
        
        for source, stats in source_stats.items():
            file.write(f"| {source} | {stats['fetched_1d']} | {stats['fetched_2d']} | {stats['shown_1d']} | {stats['shown_2d']} |\n")
        
        file.write("\n# Shown Order\n\n")
        for time, message, source in shown_order:
            formatted_time = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%b %d, %I:%M %p")
            file.write(f"- **{formatted_time}** - {message} ({source})\n")


def get_random_recent_item(db, source, days=7):
    """Returns a random item from the given source within the last `days` days, or None if none exist."""
    now = datetime.now(timezone.utc)
    cutoff_time = now - timedelta(days=days)

    # Filter messages by source and fetch time within the last `days`
    recent_items = [
        item for item in db.get("data", []) 
        if item["source"] == source and datetime.fromisoformat(item["fetched_datetime"].replace("Z", "+00:00")) >= cutoff_time
    ]

    return random.choice(recent_items) if recent_items else None
