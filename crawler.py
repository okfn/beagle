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
