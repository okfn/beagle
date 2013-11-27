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
import datetime
from scrapy.settings import CrawlerSettings
from beaglemail import sender, template

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

def send_emails():
    # Get users we want to send emails to and create the emailer
    # We piggyback on the beagleboy settings by loading and using them
    settings = CrawlerSettings(beagleboy.settings)
    users = get_users(settings)
    emailer = sender.Emailer(settings)

    # Loop through each user and compose an email to that user
    for user in users:
        # Loop through sites the user is tracking and create plain
        for site in user['sites']:

            # Get plain and html content and attach them to the message
            # The template needs site title and expected publication date
            params = {'researcher':user['name'],
                      'date':site['date'],
                      'site':site['title']}
            # We set html to True because we want both plain and html versions
            (plain, html) = template.render('scraper.email', params,
                                            user.get('lang', None), html=True)

            # Send the email with our emailer
            emailer.send(user['email'], plain, html_content=html)

if __name__ == '__main__':
    send_emails()

