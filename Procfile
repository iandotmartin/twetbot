web: gunicorn -w 1 wsgi:app
worker: rq worker --url $REDISCLOUD_URL
