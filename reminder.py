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

import gettext
import pymongo
import smtplib
import datetime
from email.mime.text import MIMEText

# We reuse the email settings from beagleboy
from beagleboy import settings

# Translations are located in the root directory
gettext.install('beagle', 'locale', unicode=True)

def get_users():
    """
    Get users from the database who's sites fall within the grace period
    and return them in a list with email addresses, names, preferred language,
    and the site titles they watch.
    """

    # Get grace period. We compute it back in time since we want to
    # find all pages which should be getting reminder emails (they get
    # reminders every week during the grace period)
    today = datetime.datetime.today()
    grace_weeks = settings.PUBLICATION_GRACE_PERIOD
    grace_period = today - datetime.timedelta(weeks=grace_weeks)

    # Connect to the MongoDB account
    connection = pymongo.MongoClient(settings.MONGODB_HOST,
                                     settings.MONGODB_PORT)
    db = connection[settings.MONGODB_DATABASE]
    
    # We only grab pages that are active and within the grace period
    # Information we need are email, name, and language
    pipeline = [
        {'$unwind': '$sites'},
        {'$match': {'sites.active': True,
                    'sites.publication_dates': {'$gte':grace_period,
                                                '$lte':today}}
         },
        {'$group': {'_id': {'email': '$_id','name':'$name','lang':'$language'}, 
                    'sites': {'$addToSet': '$sites.title'}}
         }
        ]

    # Aggregate the results and return a list of the users
    results = db.users.aggregate(pipeline)
    return [{'email':user['_id']['email'],
             'name':user['_id']['name'],
             'lang':user['_id']['lang'],
             'sites':user['sites']}\
                for user in results['result']]

def send_emails():
    # Get mail host or localhost
    host = settings.MAIL_HOST
    if not host:
        host = 'localhost'

    # Get sender or return
    sender = settings.MAIL_FROM
    if not sender:
        return
    # Get username and password for the mail server
    sender_user = settings.MAIL_USER
    sender_pass = settings.MAIL_PASS
    
    # Get users we want to send emails to
    users = get_users()

    # Connect to the SMTP host and log in if necessary
    server = smtplib.SMTP(host)
    if sender_user and sender_pass:
        server.login(sender_user, sender_pass)

    # Loop through each user and compose an email to that user
    for user in users:
        # Install the translation and default to english
        user_locale = gettext.translation(
            'beagle', 'locale',languages=[user.get('lang', 'en')])
        user_locale.install(unicode=True)

        # Email body content
        greeting = _(u"Hi {person}!").format(person=user['name'])
        reminder = _(u"This is just a friendly reminder that the budget you're assigned to watch should have been released. If it has already been released then you can ignore this message. If not, then go and check if it has been released.")
        sites = _(u"Here is what you should be specifically looking at now: {sitelist}").format(sitelist=u', '.join(user['sites']))

        content = u'\n\n'.join([greeting, reminder, sites])

        # Create the email message
        msg = MIMEText(content, _charset='utf-8')
        msg['From'] = sender
        msg['To'] = user['email']
        msg['Subject'] = _('Budget Reminder')

        # Send the email
        server.sendmail(sender, [user['email']], msg.as_string())

    server.quit()
