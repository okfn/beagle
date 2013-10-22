# -*- coding: utf-8 -*-
# beagleboy - scrape web resources for changes and notify users by email
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

import txmongo
import datetime
from collections import defaultdict
from scrapy import log
from twisted.internet import defer
from beagleboy.messages import Email

class UpdateChecker(object):
    """
    Check site items for updates by comparing checksums to those in a
    MongoDB collection. Sends out emails to users assigned with the sites
    if there are any updates.
    """

    @defer.inlineCallbacks
    def open_spider(self, spider):
        """
        Called when the spider starts (but before it crawls). This method is
        decorated with defer.inlineCallbacks because those are used when
        accessing MongoDB.
        """

        # We will need to hold all checksums and changes until the spider
        # is closed (so we won't access the database for every item)
        self.checksums = defaultdict(set)
        self.changes = defaultdict(list)        

        # Open up the database connection
        settings = spider.crawler.settings
        log.msg(spider.crawler.settings)
        self.connection = yield txmongo.MongoConnection()
        self.db = self.connection[settings.get('MONGODB_DATABASE')]

        # We use the aggregation framework to get all checksums for the sites
        pipeline = [{'$group': 
                     {'_id': '$site','checksums': {'$push': '$checksum'}} 
                   }]
        
        results = yield self.db.checksums.aggregate(pipeline)

        # We add the checksums as a set for the sites they belong to
        for result in results:
            self.checksums[result['_id']] = set(result['checksums'])

    def process_item(self, item, spider):
        """
        Process each crawled page/source and check if it has changes
        """

        try:
            # Try to get the checksum from the set
            checksum = self.checksums[item['site']].remove(item['checksum'])
            # If this leaves us with an empty set we remove the key
            # this makes handling this later much easier
            if not self.checksums[item['site']]:
                del self.checksums[item['site']]
        except KeyError:
            # If there's a key error the checksum doesn't exist (either it's
            # a new site or the site has been modified)
            if item['checksum'] not in self.checksums[item['site']]:
                # We add the site along with the url and the checksum to 
                # our changes dictionary
                self.changes[item['site']].append({
                        'url':item['url'], 'checksum': item['checksum']})

        return item

    @defer.inlineCallbacks
    def close_spider(self, spider):
        """
        Called when the spider closes (after the crawl). This goes through all
        changes, additions, and removals updates the database and sends out an
        email in case the sites have changes somehow
        """

        # Go through all changes and update the checksums
        for site, urls in self.changes.iteritems():
            for url in urls:
                # The reason we use findAndModify is that it returns the old
                # document. This means that if we want to check if this is a
                # new site the result will be None and not None if it's an
                # update to an existing url (we don't check this now)
                result = yield self.db.checksums.find_and_modify(
                    query={'site':site, 'url': url['url']},
                    update={'$set':{'checksum': url['checksum']}},
                    upsert=True)

        # Remove all sites remaining in checksums dict because the are no
        # longer accessible (not crawled)
        for site, checksums in self.checksums.iteritems():
            yield self.db.checksums.remove({
                    'site':site, 'checksum': {'$in': list(checksums)}})

        # We need to create a set of sites from changed and removed sites
        sites = set(self.changes.keys())
        sites.update(self.checksums.keys())

        # We loop through the sites that have been changed or removed to
        # send emails to the user watching them and update its time.
        for site in sites:
            # Get the user that watches this dataset
            user = yield self.db.users.find_one({'sites.url':site})
            if user is None:
                continue

            # Send an email to that user
            email = Email({'name':user['name'],
                            'email': user['_id'],
                            'lang': user['language']}, site)
            email.send()

            # Update the last_changed for that particular site in the user's
            # list of sites
            yield self.db.users.update(
                {'_id': user['_id'], 'sites.url': site},
                {'$set': {'sites.$.last_change': datetime.datetime.now()}})

        yield self.connection.disconnect()
