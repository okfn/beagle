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

import pymongo

class MongoCollection(object):
    """
    Class that talks to a MongoDB database. Upon connect it connects all the
    way down to the collection. This class should be subclassed and the 
    subclass has to be used with the python with statement:

    with SubClass(settingsobject) as subinstance:
      # do something with subinstance
    """

    def __init__(self, settings, *args, **kwargs):
        """
        Initialise the MongoDB connection with parameters from a settings
        object with the same interface as to scrapy.settings.CrawlerSettings
        """

        # Connection parameters to the MongoDB database
        self.host = settings.get('MONGODB_HOST', 'localhost')
        self.port = settings.getint('MONGODB_PORT', 27017)
        self.database = settings.get('MONGODB_DATABASE', 'beagle')

        # We initialise variables used elsewhere as None
        self.connection = None
        self.collection = None

    @property        
    def _collection(self):
        """
        The collection name, gathered from a subclass or the class name.
        Subclasses should have an attribute '__collection__' with the 
        collection name
        """

        # Try to get the model attribute of a class, if it doesn't exist
        # we just use the lowercased class name
        if hasattr(self, '__collection__'):
            return self.__collection__
        else:
            return self.__class__.__name__.lower()

    def __enter__(self):
        """
        Open up the database connection and connect to the collection
        Return self (since this class will be subclassed)
        """

        self.connection = pymongo.MongoClient(self.host, self.port)
        self.collection = self.connection[self.database][self._collection]
        return self

    def __exit__(self, type, value, traceback):
        """
        Disconnect the MongoDB database connection
        """
        self.connection.disconnect()

    def aggregate(self, pipeline):
        """
        Short hand to the aggregate of the database class
        (which is a shorthand for the real aggregation function)
        Difference is that this one knows which collection we're accessing
        This mostly only saves use the self.collection part when called from
        other functions
        """

        # Return the results (well the result of the results).
        return self.collection.aggregate(pipeline)['result']
