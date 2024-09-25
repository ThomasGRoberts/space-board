import asyncio
import os
from datetime import datetime
from typing import List
import dotenv
from twikit import Client

from logger import Logger
from vestaboard import push_to_vestaboard

# Set up logging
logging = Logger.setup_logger(__name__)

# client = GuestClient()
dotenv.load_dotenv()

# Load Twitter users from environment variable
TWITTER_USERS: List[str] = os.getenv('TWITTER_USERS').split(",")

date_format = "%a %b %d %H:%M:%S %z %Y"

# Initialize client
client = Client('en-US')

# Paste you cookies here
cookie = {
    'guest_id': 'v1%3A171587249500383020',
    'night_mode': '2',
    'guest_id_marketing': 'v1%3A171587249500383020',
    'guest_id_ads': 'v1%3A171587249500383020',
    'gt': '1837509930200584217',
    'g_state': '{"i_l":0}',
    'kdt': 'Wkjutsm01gIzfuX3h7JhIPcbjxpww956JfFe2AfF',
    'auth_token': os.getenv('TWITTER_AUTH_TOKEN'),
    'ct0': '7df6f55a48de944f41329d2dc076ab3426fa20c700fe620198d3c85b60d015112900d1b65d39047cd5fa42e3396f66a109a4681f9ce74f321d6c6ad150d8b447ca660436f58e26949c0ef81bd453d199',
    'att': '1-osXpqqB177IoiTeiHq0q2961A0wACZYNR1VnNvZM',
    'lang': 'en',
    'twid': 'u%3D1757693804226781186',
    'personalization_id': '"v1_5DUo7SIttTtK0IxUFpvxwA=="',
}

client.set_cookies(cookie)
# client.load_cookies("./cookies.json")


async def pull_from_twitter(already_pushed: List[int]):
    twitter_queue = []

    try:
        await client.user()
    except Exception as e:
        print(e)
        push_to_vestaboard("Please replace the twitter cookies :)", source="error")
        return twitter_queue

    # Fetch tweets for each user
    for user in TWITTER_USERS:
        try:
            logging.info(f"Fetching data for Twitter user: {user}")
            # user_data = await client.get_user_by_screen_name(screen_name=user)
            # user_tweets = await client.get_user_tweets(user_id=user_data.id, count=10)
            user_tweets = await client.search_tweet(query=f"from:{user} -filter:replies", product="Latest", count=10)

            logging.info(f"Retrieved {len(user_tweets)} tweets for user: {user}")

            for tweet in user_tweets[:min(11, len(user_tweets))]:
                # for tweet in user_tweets[:2]:
                created_at = datetime.strptime(tweet.created_at, date_format)
                # print(created_at)
                if created_at.date() != datetime.now(created_at.tzinfo).date():
                    # pass
                    continue
                if int(tweet.id) in already_pushed:
                    logging.info(f"Skipping already processed tweet with ID: {tweet.id}")
                    continue

                twitter_queue.append({"content": tweet.text, "user": user})
                already_pushed.append(int(tweet.id))

        except Exception as e:
            logging.error(f"Error occurred while processing user {user}: {e}")
            # raise e

    logging.info(f"Number of new tweets added to the queue: {len(twitter_queue)}")
    # client.save_cookies("./cookies.json")
    return twitter_queue

# if __name__ == "__main__":
#     asyncio.run(pull_from_twitter([]))
