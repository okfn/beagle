# Scrapy settings for beagleboy project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Beagle budget scraper (+http://)'

FORM_URL = 'http://somewhere.form'

# Mail settings
MAIL_FROM = ''
MAIL_HOST = ''
MAIL_USER = ''
MAIL_PASS = ''

# MongoDB configurations (collections are automatic so we only need the
# database name
MONGODB_DATABASE = 'beagle'

# Number of weeks to run checks and reminders after publication date
# i.e. to send out emails
PUBLICATION_GRACE_PERIOD = 4

BOT_NAME = 'beagleboy'

SPIDER_MODULES = ['beagleboy.spiders']
NEWSPIDER_MODULE = 'beagleboy.spiders'

# Check for updates to sites, send emails and update the database
ITEM_PIPELINES = [
    'beagleboy.pipelines.UpdateChecker'
]

# In case of original page is redirected we set the original url as the
# referer in followed links
SPIDER_MIDDLEWARES_BASE = {
    'beagleboy.spidermiddleware.OriginRefererMiddleware': 700,
    'scrapy.contrib.spidermiddleware.referer.RefererMiddleware': None
}
