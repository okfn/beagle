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
import beagleboy.settings
from db.collections import Countries
import urllib2
import json

def load_obi_scores():
    """
    Download the OBI scores from IBP's survey site and load them into the
    database
    """

    # We piggyback on the beagleboy settings by loading and using them
    settings = CrawlerSettings(beagleboy.settings)

    # Fetch the json file and load it's contents
    dataurl ='http://survey.internationalbudget.org/downloads/ibp_data.json'
    json_file = urllib2.urlopen(dataurl)
    data = json.loads(json_file.read())

    with Countries(settings) as countries:
        for country in data['country']:
            # Get the country name
            name = country['name']
            # Get the country scores
            scores = [{'year':k[3:], 'score':v['roundobi']}\
                          for k,v in country.iteritems()\
                          if k.startswith('db_')]
            # Write this to the database
            countries.update_scores(name, scores)

if __name__ == '__main__':
    load_obi_scores()
