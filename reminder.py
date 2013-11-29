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

from scrapy.settings import CrawlerSettings
from db.collections import Users
from beaglemail import sender, template

# We reuse the email settings from beagleboy
import beagleboy.settings

def send_emails():
    """
    Find all users who should get a reminder and send emails to them. This
    just connects two modules (beaglemail and db) and relays the information
    between them.
    """

    # We piggyback on the beagleboy settings by loading and using them
    settings = CrawlerSettings(beagleboy.settings)

    # Get users we want to send emails to and create the emailer
    emailer = sender.Emailer(settings)
    with Users(settings) as users:
        # Loop through each user and compose an email to that user
        for user in users.remindees():
            # Loop through sites the user is tracking and create plain
            for site in user['sites']:
                # Get plain and html content and attach them to the message
                # The template needs site title and expected publication date
                params = {'researcher':user['name'],
                          'date':site['date'],
                          'site':site['title']}
                # We set html to True because we want both plain and html
                (plain, html) = template.render('reminder.email', params,
                                                user.get('locale', None),
                                                html=True)

                # Send the email with our emailer
                emailer.send(user['email'], plain, html_content=html)

if __name__ == '__main__':
    send_emails()

