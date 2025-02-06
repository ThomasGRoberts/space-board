import json
from datetime import datetime, timedelta

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

CURRENT_DATE = datetime.now().strftime('%Y-%m-%d')
YESTERDAY_DATE = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')


def create_persisted_data():
    logging.info("Creating new persisted data for the current date.")
    return {
        "date": CURRENT_DATE,
        "aidy_ids": [],
        "aidy_queue": [],
        "supercluster_ids": [],
        "supercluster_queue": [],
        "spacenews_ids": [],
        "spacenews_queue": [],
        "space_ids": [],
        "space_queue": [],
        "nyt_ids": [],
        "nyt_queue": [],
        f"old_updates": [],
    }


try:
    logging.info("Loading persisted data from data.json.")
    PERSISTED_DATA = json.load(open('./data.json'))
except Exception as e:
    logging.error(f"Failed to load persisted data: {e}. Creating new data.")
    PERSISTED_DATA = create_persisted_data()

if PERSISTED_DATA["date"] != CURRENT_DATE:
    logging.info("Persisted data is from a previous date. Creating new data for today.")
    old_updates = PERSISTED_DATA["old_updates"].copy()
    old_updates = sorted(old_updates, key=lambda update: datetime.strptime(update["date"], "%Y-%m-%d"), reverse=True)[
                  :min(11, len(old_updates))]
    PERSISTED_DATA = create_persisted_data()
    PERSISTED_DATA["old_updates"] = old_updates

SOURCES = {
    "space": pull_from_space,
    "aidy": pull_from_aidy,
    "supercluster": pull_from_supercluster,
    "spacenews": pull_from_spacenews,
    "nyt": pull_from_nyt
}

def execute_steps():
    logging.info("Executing steps to process queues and fetch new data.")

    for source_name, fetch_function in SOURCES.items():
        queue_key = f"{source_name}_queue"
        ids_key = f"{source_name}_ids"

        # Ensure queue and IDs exist
        if queue_key not in PERSISTED_DATA:
            PERSISTED_DATA[queue_key] = []
        if ids_key not in PERSISTED_DATA:
            PERSISTED_DATA[ids_key] = []

        # Push from queue if available
        if PERSISTED_DATA[queue_key]:
            logging.info(f"Pushing {source_name} data to Vestaboard.")
            push_to_vestaboard(PERSISTED_DATA[queue_key][0], source=source_name,
                               old_updates=PERSISTED_DATA["old_updates"])
            PERSISTED_DATA[queue_key].pop(0)
            return

        # Fetch new data if queue is empty
        logging.info(f"Fetching {source_name} data.")
        new_queue = fetch_function(already_pushed=PERSISTED_DATA[ids_key])

        if new_queue:
            logging.info(f"Fetched {len(new_queue)} {source_name} records.")
            PERSISTED_DATA[queue_key] = new_queue
            push_to_vestaboard(PERSISTED_DATA[queue_key][0], source=source_name,
                               old_updates=PERSISTED_DATA["old_updates"])
            PERSISTED_DATA[queue_key].pop(0)
            return

    if len(PERSISTED_DATA["old_updates"]) > 0:
        push_to_vestaboard(PERSISTED_DATA["old_updates"][0]["data"], source=PERSISTED_DATA["old_updates"][0]["source"],
                           old_updates=PERSISTED_DATA["old_updates"])
        logging.info(f'Pushed old data: {PERSISTED_DATA["old_updates"][0]["data"]}')
        PERSISTED_DATA["old_updates"].pop(0)


if __name__ == "__main__":
    logging.info("Starting execution.")
    execute_steps()
    logging.info("Saving updated persisted data to data.json.")
    with open('./data.json', 'w') as f:
        json.dump(PERSISTED_DATA, f, indent=4, ensure_ascii=False)
    logging.info("Execution completed.")
