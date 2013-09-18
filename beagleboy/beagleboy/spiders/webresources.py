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

from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from beagleboy.items import WebResource
from scrapy import log
import pymongo
from beagleboy import settings
from hashlib import md5

class WebResourceSpider(CrawlSpider):
    """
    Crawl a webpage and its resources and compute the checksum for each
    resource. Return a WebResource item with the site (main page url),
    url (url of the resource) and the checksum (of the resource)
    """

    # Launch the crawler using scrapy crawl webresources
    name = "webresources"

    # We define what links we should follow and that we only go "one down".
    # So we'll only look at the web page and the content of its links (not the
    # links of the links etc.
    rules = [
        Rule(SgmlLinkExtractor(
                tags=('a', 'iframe', 'object', 'embed', 'script'),
                attrs=('href', 'src', 'data')),
             callback='parse_start_url', follow=False)
        ]

    @property
    def start_urls(self):
        """
        Get the start_urls for the spider. These are fetched from a
        database using get_user_urls()
        """
        return self.get_user_urls()

    @start_urls.setter
    def start_urls(self, value):
        """
        Since the engine sets the start_urls we overwrite the setter to do
        nothing with the value (since we will always fetch it from a database)
        """
        pass

    def get_user_urls(self):
        """
        Get the user urls from the database (this is generated for start_urls).
        This is a blocking operation since that's how scrapy accesses
        start_urls. Since this is only executed in the beginning that's fine.
        """

        # Open the database and access it based on the settings
        connection = pymongo.MongoClient()
        db = connection[settings.MONGODB_DATABASE]

        # We use the aggregation framework to get all of the sites urls
        pipeline = [
            {'$unwind': '$sites'}, 
            {'$group':{'_id':'all', 'sites': {'$addToSet':'$sites.url'}}}
            ]

        results = db.users.aggregate(pipeline)
        connection.disconnect()

        # Since we aggregate everything into all we only need the first result
        # and the sites list in that result
        return results['result'][0]['sites']
        
    def parse_start_url(self, response):
        """
        Create and return a WebResource item from a parsed url.
        URLs in 'start_urls' are automatically passed through here, but we
        also redirect other resposne here (with a rule) so this is a
        generic response parser
        """

        item = WebResource()
        # Get the main page url
        site = response.request.meta.get('redirect_urls', [response.url])[0]
        # Set the main page url (either in request header under Referer or
        # in the site variable)
        item['site'] = response.request.headers.get('Referer', site)
        # URL of this resource (if this is a start_url this will be the same
        # url as in item['site'])
        item['url'] = response.url
        # Get the checksum for the body
        item['checksum'] = md5(response.body).hexdigest()

        return item
