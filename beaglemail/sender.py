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

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class Emailer(object):
    """"
    Emailer object that sends emails using python's built-in smtplib. The
    emails can be either plain text only or both plain text and html
    """

    def __init__(self, settings, *args, **kwargs):
        """
        Initialize an email host using a settings object that provides
        the same interface as scrapy.settings.CrawlerSettings (or other
        scrapy settings). It fetches MAIL_* configurations like HOST, PORT,
        FROM, USER, and PASS. The only one of these required is MAIL_FROM
        which raises a value error if not present.
        """

        # Get mail host or localhost
        self.host = settings.get('MAIL_HOST', 'localhost')
        self.port = settings.getint('MAIL_PORT', 25)

        # Get sender or return
        self.sender = settings.get('MAIL_FROM', None)
        if not self.sender:
            raise ValueError('MAIL_FROM not set in settings')

        # Get username and password for the mail server
        self.user = settings.get('MAIL_USER', None)
        self.password = settings.get('MAIL_PASS', None)

    def send(self, to, content, html_content=None):
        """
        Send contents of an email to a provided recipient (single recipient).
        The content provided must be plain text, but html content can also
        be provided to send an altivernative email (html with fallback).
        
        Subject is taken from the email content and is always the first line
        in both the html and the plain versions (even though the subject line
        from the plain text is the one used). Email body is considered to be
        the rest of the content.
        """

        # Connect to the SMTP host and log in if necessary
        server = smtplib.SMTP(self.host, self.port)
        if self.user and self.password:
            server.login(self.user, self.password)

        # Get the subject and the plain text body
        (subject, newline, plain) = content.partition('\n')

        # Create the email itself. If html content has been provided we
        # create a MIME Multipart message, if not we send a simple MIMEText
        # UTF-8 is the default charset (non-overwriteble)
        if html_content:
            # We need to get remove the subject line from the html content too
            (_ignore, newline, html) = html_content.partition('\n')
            msg = MIMEMultipart('alternative')
            msg.attach(MIMEText(plain, 'plain', _charset='utf-8'))
            msg.attach(MIMEText(html, 'html', _charset='utf-8'))
        else:
            msg = MIMEText(plain, _charset='utf-8')

        # Assign message details and send the email
        msg['From'] = self.sender
        msg['To'] = to
        msg['Subject'] = subject

        server.sendmail(self.sender, [to], msg.as_string())
        server.quit()
