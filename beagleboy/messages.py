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

import gettext
from scrapy.settings import CrawlerSettings
from beagleboy import settings
from scrapy.mail import MailSender
from scrapy import log

from email.MIMEMultipart import MIMEMultipart
from email.MIMENonMultipart import MIMENonMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
from twisted.internet import reactor

# Translations are located in the root directory
gettext.install('beagle', 'locale', unicode=True)

class Email(object):
    """
    Class for sending emails to recipients when a site changes somehow
    in the recipients preferred language.
    """

    def __init__(self, recipient, site):
        """
        The class arguments are recipient and site. Site is a string while
        recipient is a dictionary. Recipient must include name, email and
        can include preferred language (as a locale identifier).
        """

        if 'name' not in recipient or 'email' not in recipient:
            raise KeyError('Recipient must have a name and an email address')

        self.recipient = recipient
        self.site = site
        log.msg(str(recipient))
        # Install the translation and default to english
        if recipient['lang']:
            user_locale = gettext.translation(
                'beagle', 'locale', languages=[recipient.get('lang')])
            user_locale.install(unicode=True)

    @property
    def content(self):
        """
        Content of email being sent, constructed from the initial parameters
        for the class.
        """

        # Oh this is going to get messy because we want the email to be
        # translatable into the recipient's preferred language

        # First we break the email into smaller chunks which are easier to
        # translate

        greeting = _(u"Hi {person}!").format(
            person=self.recipient['name'])

        intro = _(u"A web page you're assigned to watch ({site_url}) has been modified. Can you go and check if there is some new, relevant information on the site or if important information has been removed?").format(
            site_url=unicode(self.site))

        explanation = _(u"Sometimes the changes are not relevant to what you're assigned to look at (and often they're not even visible), but we cannot easily check for context so we notify you everytime anything happens.")

        form = _(u"If you notice any relevant modifications, please use the form at {form_url} to update the information about the web page.").format(
            form_url=unicode(settings.FORM_URL))

        # Then we return a concatenated version of the email
        return u'\n\n'.join([greeting, intro, explanation, form])

    def send(self):
        """
        Send the email to the recipient
        """
        import smtplib
        from email.mime.text import MIMEText

        crawl_settings = CrawlerSettings(settings)
        # Get mail host or localhost
        host = crawl_settings.get('MAIL_HOST', 'localhost')
        port = crawl_settings.getint('MAIL_PORT', 25)
        sender = crawl_settings.get('MAIL_FROM', None)
        # Get sender or return
        if not sender:
            return
        # Get username and password for the mail server
        sender_user = crawl_settings.get('MAIL_USER', None)
        sender_pass = crawl_settings.get('MAIL_PASS', None)
    
        # Connect to the SMTP host and log in if necessary
        server = smtplib.SMTP(host, port)
        if sender_user and sender_pass:
            server.login(sender_user, sender_pass)

        # Create the email message
        msg = MIMEText(self.content, _charset='utf-8')
        msg['From'] = sender
        msg['To'] = self.recipient['email']
        msg['Subject'] = _(u'A web page you are watching has changed')

        # Send the email
        server.sendmail(sender, [self.recipient['email']], msg.as_string())

        server.quit()
