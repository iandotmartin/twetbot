# twetbot

twetbot finds twets

### configuration
twetbot uses .env files for configuration. make sure you've installed from `requirements-dev` as `python-dotenv` is necessary for these variables to be picked up by flask.


### dev server stuff
to run a local development server with nice flask things like auto-reload, etc:

```bash
$ flask run
```

you can access the running server at http://localhost:5000

use [ngrok](https://ngrok.com/) to easily tunnel your local server so slack can see it. use the `/challenge` endpoint to verify when subscribing to events.

### deployment
tbd.

using gunicorn:
```bash
$ gunicorn -w 1 wsgi:app
```
