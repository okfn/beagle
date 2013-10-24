# -*- coding: utf-8 -*-
# beagle - scrape web resources for changes and notify users by email
# Copyright (C) 2013  The Open Knowledge Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from apscheduler.scheduler import Scheduler

from rq import Queue
from worker import conn

from crawler import crawl_webresources
from reminder import send_emails
from beagleboy import settings

# Set up queue and scheduler
q = Queue(connection=conn)
sched = Scheduler()


@sched.cron_schedule(day='last')
def crawl():
    """
    A scheduled method that runs the crawler on the last day of the month
    """
    # Enqueue via Redis queue the web resource crawler
    result = q.enqueue(crawl_webresources)

@sched.interval_schedule(minutes=2)
def reminders():
    """
    A scheduled method that sends out the email reminders every week.
    These will only send emails to those within a grace period but that's
    a part of the implementation of the function that's enqueued here
    """
    # Enqueue via Redis queue the reminder emails
    result = q.enqueue(send_emails)

# Start scheduling
sched.start()

# Run this script forever
while True:
    pass

