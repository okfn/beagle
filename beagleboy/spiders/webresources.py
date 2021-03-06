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

from scrapy.http import Request, HtmlResponse
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from beagleboy.items import WebResource
from db.collections import Users
from scrapy import log
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
    # Since WordPress sites link back to an ever changing wordpress.org site
    # we don't follow those links. This is hardcoded since no other constantly
    # changing sites are known. If there are others we will have to fish this
    # out, and read from database (which can be set via a user interface).
    rules = [
        Rule(SgmlLinkExtractor(
                tags=('a', 'iframe', 'object', 'embed', 'script'),
                attrs=('href', 'src', 'data'),
                deny=('http://wordpress.org', )),
             callback='parse_start_url', follow=False)
        ]

    @property
    def start_urls(self):
        """
        Get the start_urls for the spider. These are fetched from a
        database using get_user_urls()
        """
        # Begin by creating our database user object (synchronous is ok here)
        with Users(self.crawler.settings) as users:
            # Then we return the urls of all users
            urls = users.urls()
            # We have now seen these urls so we don't have to crawl them again
            self.seen = set([s.rstrip('/') for s in urls])
            return urls

    @start_urls.setter
    def start_urls(self, value):
        """
        Since the engine sets the start_urls we overwrite the setter to do
        nothing with the value (since we will always fetch it from a database)
        """
        pass

    def _requests_to_follow(self, response):
        """
        Overwritten _requests_to_follow since we want to use a global seen
        and not a new one everytime so we won't follow the same urls again
        """

        if not isinstance(response, HtmlResponse):
            return

        for n, rule in enumerate(self._rules):
            # We only add links which have never been seen
            # We need to rstrip / because we don't know if the links have
            # a trailing slash
            links = [l for l in rule.link_extractor.extract_links(response)\
                         if l.url.rstrip('/') not in self.seen]
            if links and rule.process_links:
                links = rule.process_links(links)
            # Update self.seen - we add the url only (remove trailing slash)
            self.seen = self.seen.union([l.url.rstrip('/') for l in links])
            for link in links:
                r = Request(url=link.url, callback=self._response_downloaded)
                r.meta.update(rule=n, link_text=link.text)
                yield rule.process_request(r)
        
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
