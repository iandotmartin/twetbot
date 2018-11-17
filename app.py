import os

import requests
from flask import Flask
from flask import request

from twet import APIClient


app = Flask(__name__)
twitter = APIClient()


@app.route('/challenge', methods=['GET', 'POST'])
def challenge():
    challenge = request.json.get('challenge')

    return challenge or 'no challenge, huh?!'


@app.route('/', methods=['GET', 'POST'])
def say_hi():
    return "booya"


@app.route('/dril', methods=['POST'])
def dril_twet():
    query = request.form.get('text')

    if not query:
        return """i approve of congres... i believe they are doing a very good job despite negative comments online

        p.s. enter a query next time"""

    response_url = request.form.get('response_url')

    # send initial response to slack

    data = {
        "text": f"lookin for {query}",
        "attachments": [
            {
                "text":"B-)"
            }
        ]
    }
    resp = requests.post(response_url, json=data)
    send_tweet_options(query, response_url)

    return 'ok', 204


@app.route('/dril/choose', methods=['POST'])
def choose_and_post_tweet():
    # gets a twitter url or id of some sort
    # deletes original message and posts embeddable url to a given slack room
    return "ok"


def send_tweet_options(query, response_url):
    tweets = twitter.get_good_tweets(query)

    headers = {'Content-type':'application /json'}
    data = {
        "text": f"here's your awful tweets",
        "attachments": format_tweet_summaries(tweets)
    }
    resp = requests.post(response_url, json=data, headers=headers)


def format_tweet_summaries(tweets):
    # TODO: Format Slack Message Nicely.
    # We'll need to make it so this message has clickable buttons so users
    # can choose the twet that they'd like to embed. for now this probably sucks so lets go
    slack_formatted_tweets = []
    for tweet in tweets:
        slack_formatted_tweets.append({
            "text": tweet.text,
            "callback_id": tweet.id,
            "actions": [
                {
                    "name": "select",
                    "text": "select, this awful post",
                    "type": "button",
                    "value": "select"
                },
            ]
        })

    return slack_formatted_tweets

