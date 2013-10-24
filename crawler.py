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

from twisted.internet import reactor
from scrapy.crawler import Crawler
from scrapy import log, signals
from scrapy.settings import CrawlerSettings

from beagleboy.spiders.webresources import WebResourceSpider
import beagleboy.settings

def crawl_webresources():
    """
    Crawl web resources using the beagleboy webresource spider.
    This methods should be queued to be run as a background process.
    """
    
    # Create a crawler with the beagleboy settings
    crawler = Crawler(CrawlerSettings(settings_module=beagleboy.settings))
    # Add a signal to stop the reactor when the spider closes
    crawler.signals.connect(reactor.stop, signal=signals.spider_closed)
    # Configure the crawler
    crawler.configure()

    # Create a web resource spider and add that as the crawler
    spider = WebResourceSpider()
    crawler.crawl(spider)

    # Start crawling and logging
    crawler.start()
    log.start()

    # Run the reactor (this block until spider closes)
    reactor.run()
