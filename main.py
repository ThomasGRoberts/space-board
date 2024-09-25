import asyncio
import json
import random
from datetime import datetime, timedelta

from dotenv import load_dotenv

from aidy import pull_from_aidy
from logger import Logger
from spacenews import pull_from_spacenews
from supercluster import pull_from_supercluster
from twitter import pull_from_twitter
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
        "twitter_ids": [],
        "twitter_queue": [],
        f"old_updates": [],
        # f"old_old_updates": []
    }


try:
    logging.info("Loading persisted data from data.json.")
    PERSISTED_DATA = json.load(open('./data.json'))
except Exception as e:
    logging.error(f"Failed to load persisted data: {e}. Creating new data.")
    PERSISTED_DATA = create_persisted_data()

if PERSISTED_DATA["date"] != CURRENT_DATE:
    logging.info("Persisted data is from a previous date. Creating new data for today.")
    # old_old_updates = PERSISTED_DATA["old_updates"].copy()
    old_updates = PERSISTED_DATA["old_updates"].copy()
    old_updates = sorted(old_updates, key=lambda update: datetime.strptime(update["date"], "%Y-%m-%d"), reverse=True)[
                  :min(11, len(old_updates))]
    PERSISTED_DATA = create_persisted_data()
    # PERSISTED_DATA["old_old_updates"] = old_old_updates
    PERSISTED_DATA["old_updates"] = old_updates


def execute_steps():
    logging.info("Executing steps to process queues and fetch new data.")

    if len(PERSISTED_DATA["aidy_queue"]) > 0:
        logging.info("Pushing AIDY data to Vestaboard.")
        push_to_vestaboard(PERSISTED_DATA["aidy_queue"][0], source="aidy", old_updates=PERSISTED_DATA["old_updates"])
        PERSISTED_DATA["aidy_queue"].pop(0)
        return

    logging.info("Fetching AIDY data.")
    aidy_queue = pull_from_aidy(already_pushed=PERSISTED_DATA["aidy_ids"])

    if len(aidy_queue) > 0:
        logging.info(f"Fetched {len(aidy_queue)} AIDY records.")
        PERSISTED_DATA["aidy_queue"] = aidy_queue
        push_to_vestaboard(PERSISTED_DATA["aidy_queue"][0], source="aidy", old_updates=PERSISTED_DATA["old_updates"])
        PERSISTED_DATA["aidy_queue"].pop(0)
        return

    if len(PERSISTED_DATA["supercluster_queue"]) > 0:
        logging.info("Pushing Supercluster data to Vestaboard.")
        push_to_vestaboard(PERSISTED_DATA["supercluster_queue"][0], source="supercluster",
                           old_updates=PERSISTED_DATA["old_updates"])
        PERSISTED_DATA["supercluster_queue"].pop(0)
        return

    logging.info("Fetching Supercluster data.")
    supercluster_queue = pull_from_supercluster(already_pushed=PERSISTED_DATA["supercluster_ids"])

    if len(supercluster_queue) > 0:
        logging.info(f"Fetched {len(supercluster_queue)} Supercluster records.")
        PERSISTED_DATA["supercluster_queue"] = supercluster_queue
        push_to_vestaboard(PERSISTED_DATA["supercluster_queue"][0], source="supercluster",
                           old_updates=PERSISTED_DATA["old_updates"])
        PERSISTED_DATA["supercluster_queue"].pop(0)
        return

    if len(PERSISTED_DATA["spacenews_queue"]) > 0:
        logging.info("Pushing SpaceNews data to Vestaboard.")
        push_to_vestaboard(PERSISTED_DATA["spacenews_queue"][0], source="spacenews",
                           old_updates=PERSISTED_DATA["old_updates"])
        PERSISTED_DATA["spacenews_queue"].pop(0)
        return

    logging.info("Fetching SpaceNews data.")
    spacenews_queue = pull_from_spacenews(already_pushed=PERSISTED_DATA["spacenews_ids"])

    if len(spacenews_queue) > 0:
        logging.info(f"Fetched {len(spacenews_queue)} SpaceNews records.")
        PERSISTED_DATA["spacenews_queue"] = spacenews_queue
        push_to_vestaboard(PERSISTED_DATA["spacenews_queue"][0], source="spacenews",
                           old_updates=PERSISTED_DATA["old_updates"])
        PERSISTED_DATA["spacenews_queue"].pop(0)
        return

    if len(PERSISTED_DATA["twitter_queue"]) > 0:
        logging.info("Pushing Twitter data to Vestaboard.")
        push_to_vestaboard(PERSISTED_DATA["twitter_queue"][0], "twitter", old_updates=PERSISTED_DATA["old_updates"])
        PERSISTED_DATA["twitter_queue"].pop(0)
        return

    logging.info("Fetching Twitter data.")
    twitter_queue = asyncio.run(pull_from_twitter(already_pushed=PERSISTED_DATA["twitter_ids"]))

    if twitter_queue is None:
        return

    if len(twitter_queue) > 0:
        logging.info(f"Fetched {len(twitter_queue)} Twitter records.")
        PERSISTED_DATA["twitter_queue"] = twitter_queue
        push_to_vestaboard(PERSISTED_DATA["twitter_queue"][0], "twitter", old_updates=PERSISTED_DATA["old_updates"])
        PERSISTED_DATA["twitter_queue"].pop(0)
        return

    logging.info(f"No new data to push. Persisted data: {PERSISTED_DATA}")
    logging.info(f"Cycling through old data ...")

    if len(PERSISTED_DATA["old_updates"]) > 0:
        push_to_vestaboard(PERSISTED_DATA["old_updates"][0]["data"], source=PERSISTED_DATA["old_updates"][0]["source"],
                           old_updates=PERSISTED_DATA["old_updates"])
        print(f'Pushed old data: {PERSISTED_DATA["old_updates"][0]["data"]}')
        PERSISTED_DATA["old_updates"].pop(0)
    # try:
    # random_data = random.choice(PERSISTED_DATA[random.choice(["old_updates", "old_old_updates"])])
    # push_to_vestaboard(random_data["data"], source=random_data["source"])
    # except Exception as e:
    #     logging.error(str(e))
    #     logging.error("Most probably You don")


if __name__ == "__main__":
    logging.info("Starting execution.")
    execute_steps()
    logging.info("Saving updated persisted data to data.json.")
    json.dump(PERSISTED_DATA, open('./data.json', 'w'))
    logging.info("Execution completed.")
