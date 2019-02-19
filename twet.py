from datetime import date
import os

from twitterscraper import query_tweets


class APIClient:

    def get_good_tweets(self, query):
        result_tweets_json = query_tweets(f"{query} from:dril", limit=10, begindate=date(2008, 9, 1))

        return result_tweets_json
