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
from reminder import budget_reminder, report_reminder
from loader import load_obi_scores
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
    result = q.enqueue(budget_reminder)

@sched.cron_schedule(day='last mon')
def report_last_monday():
    """
    A scheduled method to send out reminders about monthly report. These
    reminders should be sent out on the monday before the first friday of
    every month. This method covers the case where that monday is in the
    previous month and is complemented by the method report_first_monday.
    """

    # Get today and the friday (which is in 4 days)
    today = datetime.date.today()
    friday = today + datetime.timedelta(days=4)
    # If the friday is in the next month that's the first friday of the month
    # because this is the last monday of this month so we send out a reminder
    if friday.month != today.month:
        # We send in the date when the report is due (friday)
        result = q.enqueue(report_reminder, friday)

@sched.cron_schedule(day='1st mon')
def report_first_monday():
    """
    A scheduled method to send out reminders about monthly report. These
    reminders should be sent out on the monday before the first friday of
    every month. This method covers the case where that monday is in the
    same month and is complemented by the method report_last_monday.
    """

    # Get today and the last friday (which is 3 days ago)
    today = datetime.date.today()
    friday = today - datetime.timedelta(days=3)
    # If last friday is in the previous month the next one is the first friday
    # of this month because this is the first monday of this month so we send
    # out a reminder
    if friday.month != today.month:
        # We send in the date when the report is due (next friday)
        result = q.enqueue(report_reminder, today+datetime.timedelta(days=4))

@sched.cron_schedule(day='1st fri')
def report_first_friday():
    """
    A scheduled method to send out reminders that the monthly report is due
    today (on the first Friday of the month).
    """

    result = q.enqueue(report_due)

@sched.interval_schedule(weeks=4)
def load_scores():
    """
    A scheduled method to load the OBI scores into the database. This happens
    every four weeks (the source is updated every two years so we just want
    to check and update if it's new and be reasonably quick about it
    """

    result = q.enqueue(load_obi_scores)

# Start scheduling
sched.start()

# Run this script forever
while True:
    pass

