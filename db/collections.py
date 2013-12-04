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

from db.mongo import MongoCollection
import datetime

class Users(MongoCollection):
    """
    The users collection stores all users, information about them, and the
    sites they follow and should get notified about
    """

    __collection__ = 'users'

    def __init__(self, settings, *args, **kwargs):
        """
        Overwrite the MongoCollection __init__ to store settings in an instance
        variable, self.settings
        """

        self.settings = settings
        super(Users,self).__init__(settings, *args, **kwargs)

    def all(self, filters={}):
        """
        Get all users (they can be filtered via a parameter value
        """

        # Get the user list and if none are found return an empty list
        users = list(self.collection.find(filters))

        # If no users are found we return an empty list
        if users is None:
            return []

        # Rename _id key to email and return users
        for user in users:
            user['email'] = user.pop('_id')

        return users

    def remindees(self):
        """
        Get users from the database who's sites fall within the grace period
        and return them in a list with email addresses, names, preferred 
        language, and the site titles they watch.

        Output is a list of dictionaries for each user found and the sites that
        that fall are in the grace period.
        """

        # Get grace period. We compute it back in time since we want to
        # find all pages which should be getting reminder emails (they get
        # reminders every week during the grace period)
        today = datetime.datetime.today()
        grace_weeks = self.settings.getint('PUBLICATION_GRACE_PERIOD', 4)
        grace_period = today - datetime.timedelta(weeks=grace_weeks)

        # We only grab pages that are active and within the grace period
        # Information we need are email, name, and language
        pipeline = [{'$unwind': '$sites'}, 
                    {'$unwind': '$sites.publication_dates'},
                    {'$match': {'sites.active': True, 
                                'sites.publication_dates._d': 
                                {'$gte':grace_period, '$lte':today}}},
                    {'$group': {'_id': 
                                {'email': '$_id','name':'$name',
                                 'lang':'$language'}, 
                                'sites': {'$addToSet': 
                                          {'title':'$sites.title', 
                                           'date':'$sites.publication_dates._d'
                                           }}}
                    }]
        
        # Aggregate the results and return a list of the users
        return [{'email':user['_id']['email'],
                 'name':user['_id']['name'],
                 'locale':user['_id']['lang'],
                 'sites':user['sites']} for user in self.aggregate(pipeline)]

    def urls(self):
        """
        Get the user urls from the database as a list of strings (urls).
        """

        # We use the aggregation framework to get all of the sites urls
        # We only grab the active sites where there is a url
        pipeline = [{'$unwind': '$sites'},
                    {'$match': {'sites.active':True, 
                                'sites.url':{'$ne':None}}},
                    {'$group': {'_id':'all', 
                                'sites': {'$addToSet':'$sites.url'}}
                     }]

        # Since we aggregate everything into all we only need the first result
        # and the sites list in that result
        results = self.aggregate(pipeline)
        return results[0]['sites'] if len(results) else []

    def touch(self, site):
        """
        No this is not named so because we're trying to be funny about the
        python convention of 'self'. This is a reference to the *nix command
        touch. This updates the last_changed variable for the site for all 
        users.
        """

        # We set multi to true since there might be many users for the same site
        self.collection.update({'sites.url': site}, 
                               {'$set': {'sites.$.last_change':\
                                             datetime.datetime.now()}}, 
                               multi=True)


class Checksums(MongoCollection):
    """
    The checksums collection stores the checksums for all linked urls for
    sites that are stored (and the site itself).
    """

    __collection__ = 'checksums'

    def all(self):
        """
        Get all checksums of all sites in the collection
        """

        # We use the aggregation framework to get all checksums for the sites
        pipeline = [{'$group': {'_id': '$site',
                                'checksums': {'$push': '$checksum'}}
                     }]

        # Create a dictionary where the site url is the key with a set of
        # all checksums for that site as the value
        return {r['_id']:set(r['checksums']) for r in self.aggregate(pipeline)}

    def update(self, site, url, checksum):
        """
        Update a checksum as the value for a site, url combination in the
        database collection.
        """

        # The reason we use findAndModify is that it returns the old
        # document. This means that if we want to check if this is a
        # new insertion the result will be None and not None if it's an
        # update to an existing document
        return self.collection.find_and_modify(query={'site':site, 'url': url},
                                               update={'checksum': checksum},
                                               upsert=True)

    def remove(self, site, checksums):
        """
        Remove any url for a given site that has a checksum which is in
        the provided checksum list. 
        """
        self.collection.remove({'site':site, 'checksum': {'$in': checksums}})

class Countries(MongoCollection):
    """
    The countries collection stores information about countries, such as the
    OBI score
    """

    __collection__ = 'countries'

    def update_scores(self, country, scores):
        """
        Upsert the database scores for a given country. We only update if
        the scores have changed.
        """
        # Scores must be sorted by year
        sorted_scores = sorted(scores, key=lambda x: x['year'])
        # Update the scores if their are some new ones (or insert)
        self.collection.update({'country':country,
                                'scores': {'$ne': sorted_scores}},
                               {'$set': {'scores':sorted_scores}},
                               upsert=True)
        
