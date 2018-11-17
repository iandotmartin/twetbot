import os

from twitterscraper import query_tweets


class APIClient:

    # def __init__(self):
    #   # turns out this api sucks
    #   self.client = twitter.Api(consumer_key=os.environ.get('TWITTER_CONSUMER_KEY'),
    #                           consumer_secret=os.environ.get('TWITTER_CONSUMER_SECRET'),
    #                           access_token_key=os.environ.get('TWITTER_ACCESS_TOKEN_KEY'),
    #                           access_token_secret=os.environ.get('TWITTER_ACCESS_TOKEN_SECRET'))

    def get_good_tweets(self, query):
        # result_tweets = self.client.GetSearch(raw_query=f"f=tweets&q={query}%20from%3Adril")

        result_tweets_json = query_tweets(f"{query} from:dril", 10)

        return result_tweets_json
