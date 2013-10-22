from apscheduler.scheduler import Scheduler

from rq import Queue
from worker import conn

from crawler import crawl_webresources

# Set up queue and scheduler
q = Queue(connection=conn)
sched = Scheduler()

@sched.interval_schedule(weeks=1, misfire_grace_time=3600)
def timed_crawl():
    """
    A scheduled method that runs the crawler every week
    with time allowed to be run of one hour.
    """
    # Enqueue via Redis queue the web resource crawler
    result = q.enqueue(crawl_webresources)

# Start scheduling
sched.start()

# Run this script forever
while True:
    pass

