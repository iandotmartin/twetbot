import json
import os
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from flask import Flask
from flask import request
from redis import Redis
from rq import Queue
from slackclient import SlackClient

from twet import APIClient


load_dotenv()

app = Flask(__name__)

slack_token = os.environ["SLACK_API_TOKEN"]
sc = SlackClient(slack_token)

twitter = APIClient()

if os.environ.get('REDISCLOUD_URL'):
    redis_url = urlparse(os.environ.get('REDISCLOUD_URL'))
    redis_client = redis.Redis(host=redis_url.hostname, port=redis_url.port, password=redis_url.password)
else:
    redis_client = Redis()

q = Queue(connection=redis_client)



@app.route("/", methods=["GET", "POST"])
def challenge():
    return request.json.get("challenge")


@app.route("/actions", methods=["GET", "POST"])
def actions():
    payload = json.loads(request.form["payload"])
    # clean up message where button was pressed
    data = {
        "response_type": "ephemeral",
        "text": "",
        "replace_original": True,
        "delete_original": True,
    }
    requests.post(payload["response_url"], json=data)
    channel_id = payload["channel"]["id"]

    if payload["callback_id"].startswith("select_tweet"):
        tweet_id = payload["callback_id"].lstrip("select_tweet_")
        sc.api_call(
            "chat.postMessage",
            channel=channel_id,
            text=f"http://twitter.com/dril/status/{tweet_id}",
        )

    return "ok", 204


@app.route("/dril", methods=["POST"])
def dril_twet():
    query = request.form.get("text")
    channel_id = request.form.get("channel_id")
    user_id = request.form.get("user_id")

    if not query:
        return """i approve of congres... i believe they are doing a very good job despite negative comments online

        p.s. enter something to search for next time"""

    q.enqueue(send_tweet_options, args=[query, channel_id, user_id], timeout="60s")

    return "ok", 204


def send_tweet_options(query, channel_id, user_id):
    tweets = twitter.get_good_tweets(query)
    top_tweets = sorted(tweets, key=lambda tweet: tweet.likes, reverse=True)
    tweet_attachments = format_tweet_summaries(top_tweets[:10])
    cancel_button = {
        "text": "",
        "callback_id": "cancel_button",
        "actions": [
            {
                "text": "every post is terrible. just terrible",
                "name": "cancel",
                "type": "button",
                "style": "danger",
            }
        ],
    }
    tweet_attachments.append(cancel_button)

    sc.api_call(
        "chat.postEphemeral",
        channel=channel_id,
        user=user_id,
        text="select a musing...",
        attachments=tweet_attachments,
    )


def format_tweet_summaries(tweets):
    slack_formatted_tweets = []
    max_attachment_length = 70
    for tweet in tweets:
        tweet_stats = f"♥️ {tweet.likes} ♻️ {tweet.retweets}"
        snippet_length = max_attachment_length - len(tweet_stats)

        tweet_snippet = tweet.text.replace('\n', ' ')
        if len(tweet.text) > snippet_length:
            tweet_snippet = f"{tweet_snippet[:snippet_length-10].strip()}...".ljust(snippet_length)
        else:
            tweet_snippet = tweet_snippet.ljust(snippet_length)

        slack_formatted_tweets.append(
            {
                "text": f"```{tweet_snippet}{tweet_stats}```",
                "callback_id": f"select_tweet_{tweet.id}",
                "actions": [
                    {
                        "name": "select",
                        "text": "select, this awful post",
                        "type": "button",
                        "value": "select",
                        "style": "primary",
                    }
                ],
            }
        )

    return slack_formatted_tweets
