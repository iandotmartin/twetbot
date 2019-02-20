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

if os.environ.get("REDISCLOUD_URL"):
    redis_url = urlparse(os.environ.get("REDISCLOUD_URL"))
    redis_client = Redis(
        host=redis_url.hostname, port=redis_url.port, password=redis_url.password
    )
else:
    redis_client = Redis()

q = Queue(connection=redis_client)


@app.route("/", methods=["GET", "POST"])
def challenge():
    return request.json.get("challenge")


@app.route("/actions", methods=["POST"])
def actions():
    payload = json.loads(request.form["payload"])
    q.enqueue(post_tweet_to_channel, args=[payload], timeout="10s")
    return "ok", 204


def post_tweet_to_channel(payload):
    # clean up message where button was pressed
    data = {
        "response_type": "ephemeral",
        "text": "",
        "replace_original": True,
        "delete_original": True,
    }
    requests.post(payload["response_url"], json=data)
    channel_id = payload["channel"]["id"]

    # post tweet if selected
    if payload["callback_id"].startswith("select_tweet"):
        tweet_id = payload["callback_id"].lstrip("select_tweet_")
        resp = sc.api_call(
            "chat.postMessage",
            channel=channel_id,
            text=f"http://twitter.com/dril/status/{tweet_id}",
        )
        print(f"Tweet posted: {resp}")


@app.route("/dril", methods=["POST"])
def dril_twet():
    query = request.form.get("text")
    channel_id = request.form.get("channel_id")
    user_id = request.form.get("user_id")

    if not query:
        return """i approve of congres... i believe they are doing a very good job despite negative comments online

        p.s. enter something to search for next time"""

    q.enqueue(send_tweet_options, args=[query, channel_id, user_id], timeout="20s")

    return "ok", 204


def send_tweet_options(query, channel_id, user_id):
    tweets = twitter.get_good_tweets(query)
    top_tweets = sorted(tweets, key=lambda tweet: tweet.likes, reverse=True)
    tweet_attachments = format_tweet_summaries(top_tweets[:8], query)
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

    resp = sc.api_call(
        "chat.postEphemeral",
        channel=channel_id,
        user=user_id,
        text="select a musing...",
        attachments=tweet_attachments,
    )
    print(f"Tweet options sent: {resp}")


def format_tweet_summaries(tweets, query):
    slack_formatted_tweets = []
    for tweet in tweets:
        tweet_snippet = extract_tweet_snippet(tweet, query)

        slack_formatted_tweets.append(
            {
                "text": tweet_snippet,
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


def extract_tweet_snippet(tweet, query):
    max_attachment_line_length = 140
    tweet_stats = f"♥️{tweet.likes}"
    # snippet_length = max_attachment_line_length - len(tweet_stats) - 5 # padding
    snippet_length = max_attachment_line_length

    tweet_text = tweet.text.replace("\n", " ")
    query_index = tweet_text.find(query)
    if query_index >= 0 and len(tweet_text) > snippet_length:
        # center snippet around query
        l_index = int(query_index-(snippet_length/2))
        r_index = int(query_index+(snippet_length/2))
        if l_index <= 0:
            # no need to trim beginning
            tweet_snippet = tweet_text[:snippet_length-3].strip() + "..."
        elif r_index >= len(tweet_text):
            # no need to trim end
            tweet_snippet = "..." + tweet_text[l_index+3:].strip()
        else:
            # we're in the middle, gotta trim both
            tweet_snippet = "..." + tweet_text[l_index+3:r_index-3].strip() + "..."
    else:
        if len(tweet_text) > snippet_length:
            # maybe we missed on locating our query and it's still real long?
            tweet_snippet = f"{tweet_text[:snippet_length-3].strip()}...".ljust(snippet_length)
        else:
            # otherwise our whole tweet text fits in there nicely
            tweet_snippet = tweet_text.ljust(snippet_length)

    if query_index >= 0:
        # bold the query term
        pre_query_snip, post_query_snip = tweet_snippet.split(query, maxsplit=1)
        tweet_snippet = f"{pre_query_snip.strip()} *{query}* {post_query_snip.strip()}"

    return tweet_snippet
    # return f"{tweet_snippet} {tweet_stats}"
