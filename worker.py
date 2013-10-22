import os

import redis
from rq import Worker, Queue, Connection

# We only listen to the default queue
listen = ['default']

# Get environment variable REDISTOGO_URL and connect to it
redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
conn = redis.from_url(redis_url)

if __name__ == '__main__':
    # Run the worker and start accepting work requests
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
