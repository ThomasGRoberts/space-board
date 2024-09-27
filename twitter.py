import asyncio
import os
import re
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
    'guest_id': 'v1%3A172426559128850465',
    'night_mode': '2',
    'guest_id_marketing': 'v1%3A172426559128850465',
    'guest_id_ads': 'v1%3A172426559128850465',
    'g_state': '{"i_l":0}',
    'kdt': 'evBaS3m8S5EmFG7DgFu2VDuPqot6P8av6fx4KZNM',
    'auth_token': os.getenv('TWITTER_AUTH_TOKEN'),
    'ct0': '463dcf32b02bc2d0a3e9da0a70e863b8aac210ff1497de89644af8a820c42dc845ebcbf19a386d07b48e9aa36a16abb33c1fdb33c6b8b5663c5de216cccf432f514afcf3e9e0edf59af6233cff28df5c',
    'twid': 'u%3D1703786078',
    'lang': 'en',
    'external_referer': "padhuUp37zjgzgv1mFWxJ12Ozwit7owX|0|8e8t2xd8A2w%3D",
    'personalization_id': '"v1_cBbYwHQP02VVSDjHXvBNEg=="'
}

client.set_cookies(cookie)
print(cookie)


# client.load_cookies("./cookies.json")


async def pull_from_twitter(already_pushed: List[int]):
    twitter_queue = []

    try:
        await client.user()
    except Exception as e:
        print(e)
        push_to_vestaboard("Please replace the twitter cookies :)", source="error", old_updates=[])
        return None

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

                cleaned_content = re.sub(r'\\u[0-9A-Fa-f]{4}', '', tweet.text)
                cleaned_content = cleaned_content.strip()
                if len(cleaned_content) == 0:
                    continue
                twitter_queue.append({"content": cleaned_content, "user": user})
                already_pushed.append(int(tweet.id))

        except Exception as e:
            logging.error(f"Error occurred while processing user {user}: {e}")
            # raise e

    logging.info(f"Number of new tweets added to the queue: {len(twitter_queue)}")
    # client.save_cookies("./cookies.json")
    return twitter_queue

# if __name__ == "__main__":
#     asyncio.run(pull_from_twitter([]))
