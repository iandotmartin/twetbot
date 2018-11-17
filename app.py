from flask import Flask
from flask import request


app = Flask(__name__)


@app.route('/challenge', methods=['GET', 'POST'])
def challenge():
    challenge = request.json.get('challenge')

    return challenge or 'no challenge, huh?!'

@app.route('/', methods=['GET', 'POST'])
def say_hi():
    return "booya"
