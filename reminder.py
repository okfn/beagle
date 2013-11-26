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
from scrapy.settings import CrawlerSettings

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# We reuse the email settings from beagleboy
import beagleboy.settings

# Translations are located in the root directory
gettext.install('beagle', 'locale', unicode=True)

def get_users(settings):
    """
    Get users from the database who's sites fall within the grace period
    and return them in a list with email addresses, names, preferred language,
    and the site titles they watch.
    """

    # Get grace period. We compute it back in time since we want to
    # find all pages which should be getting reminder emails (they get
    # reminders every week during the grace period)
    today = datetime.datetime.today()
    grace_weeks = settings.getint('PUBLICATION_GRACE_PERIOD', 4)
    grace_period = today - datetime.timedelta(weeks=grace_weeks)

    # Connect to the MongoDB account
    connection = pymongo.MongoClient(settings.get('MONGODB_HOST', 'localhost'),
                                     settings.getint('MONGODB_PORT', 27017))
    db = connection[settings.get('MONGODB_DATABASE', 'beagle')]
    
    # We only grab pages that are active and within the grace period
    # Information we need are email, name, and language
    pipeline = [
        {'$unwind': '$sites'},
        {'$unwind': '$sites.publication_dates'},
        {'$match': {'sites.active': True,
                    'sites.publication_dates._d': {'$gte':grace_period,
                                                   '$lte':today}}
         },
        {'$group': {'_id': {'email': '$_id','name':'$name','lang':'$language'}, 
                    'sites': {
                    '$addToSet': {'title':'$sites.title',
                                  'date':'$sites.publication_dates._d'}
                              }
                    }
         }
        ]

    # Aggregate the results and return a list of the users
    results = db.users.aggregate(pipeline)
    return [{'email':user['_id']['email'],
             'name':user['_id']['name'],
             'lang':user['_id']['lang'],
             'sites':user['sites']}\
                for user in results['result']]

def get_message_content(name, date, site, _format='plain'):
    """
    Get email contents either as plain text of html format
    """

    # Format date to show year and month
    date = date.strftime('%Y-%m-%d')

    # If request format is html we wrap date and site title in a strong tag
    if _format == 'html':
        emphasis = '<strong>{0}</strong>'
        date = emphasis.format(date)
        site = emphasis.format(site)

    # Email body content
    greeting = _(u"Hi {person}!").format(person=name)
    reminder = _(u"This is just a friendly reminder that according to your country's budget calendar one of the budget documents you're assigned to track should have been released by {date}. If you have already checked the relevant web page and reported on the Tracker that it has been released, then you can ignore this message. If not, then please check if it has been released.").format(date=date)
    site_listing = _(u"The specific document that you are looking for is: {site}.").format(site=site)

    if _format == 'html':
        wrapper = u'<html><head></head><body><p>{0}</p></body></html>'
        body = u'</p><p>'.join([greeting, reminder, site_listing])
        return wrapper.format(body)
    else:
        return u'\n\n'.join([greeting, reminder, site_listing])

def send_emails():
    # Get mail host or localhost
    settings = CrawlerSettings(beagleboy.settings)
    host = settings.get('MAIL_HOST', 'localhost')
    port = settings.getint('MAIL_PORT', 25)
    # Get sender or return
    sender = settings.get('MAIL_FROM', None)
    if not sender:
        return
    # Get username and password for the mail server
    sender_user = settings.get('MAIL_USER', None)
    sender_pass = settings.get('MAIL_PASS', None)
    
    # Get users we want to send emails to
    users = get_users(settings)

    # Connect to the SMTP host and log in if necessary
    server = smtplib.SMTP(host, port)
    if sender_user and sender_pass:
        server.login(sender_user, sender_pass)

    # Loop through each user and compose an email to that user
    for user in users:
        if user.get('lang', None):
            # Install the translation and default to english
            user_locale = gettext.translation(
                'beagle', 'locale',languages=[user.get('lang')])
            user_locale.install(unicode=True)
        
        # Loop through sites the user is tracking and create plain
        for site in user['sites']:
            # Create the email message. We want to send in both html and
            # plain text so we need a MIME Multipart
            msg = MIMEMultipart('alternative')
            msg['From'] = sender
            msg['To'] = user['email']
            msg['Subject'] = _('Budget Reminder: {site}').\
                format(site=site['title'])

            # Get plain and html content and attach them to the message
            plain_content = get_message_content(user['name'], site['date'],
                                                site['title'])
            msg.attach(MIMEText(plain_content, 'plain', _charset='utf-8'))
            html_content = get_message_content(user['name'], site['date'],
                                                site['title'], _format='html')
            msg.attach(MIMEText(html_content, 'html', _charset='utf-8'))

            # Send the email
            server.sendmail(sender, [user['email']], msg.as_string())

        server.quit()

if __name__ == '__main__':
    send_emails()

