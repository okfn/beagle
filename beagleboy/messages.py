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

class BeagleSender(MailSender):
    """
    Class that inherits from scrapy's MailSender only to set charset as utf-8.
    The only method overwritten is send, where we add charset='utf-8' to
    either the MIMEText instance or the payload of a MIMENonMultipart instance
    """

    def send(self, to, subject, body, cc=None, attachs=(), _callback=None):
        if attachs:
            msg = MIMEMultipart()
        else:
            msg = MIMENonMultipart('text', 'plain')
        msg['From'] = self.mailfrom
        msg['To'] = COMMASPACE.join(to)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject
        rcpts = to[:]
        if cc:
            rcpts.extend(cc)
            msg['Cc'] = COMMASPACE.join(cc)

        if attachs:
            msg.attach(MIMEText(body, charset='utf-8'))
            for attach_name, mimetype, f in attachs:
                part = MIMEBase(*mimetype.split('/'))
                part.set_payload(f.read())
                Encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment; filename="%s"' \
                    % attach_name)
                msg.attach(part)
        else:
            msg.set_payload(body, charset='utf-8')

        if _callback:
            _callback(to=to, subject=subject, body=body, cc=cc, attach=attachs, msg=msg)

        if self.debug:
            log.msg(format='Debug mail sent OK: To=%(mailto)s Cc=%(mailcc)s Subject="%(mailsubject)s" Attachs=%(mailattachs)d',
                    level=log.DEBUG, mailto=to, mailcc=cc, mailsubject=subject, mailattachs=len(attachs))
            return

        dfd = self._sendmail(rcpts, msg.as_string())
        dfd.addCallbacks(self._sent_ok, self._sent_failed,
            callbackArgs=[to, cc, subject, len(attachs)],
            errbackArgs=[to, cc, subject, len(attachs)])
        reactor.addSystemEventTrigger('before', 'shutdown', lambda: dfd)
        return dfd

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
        
        # Install the translation and default to english
        user_locale = gettext.translation(
            'beagle', 'locale',languages=[recipient.get('lang', 'en')])
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
        Send the email to the recipient (via BeagleSender to force utf-8
        charset for the email
        """
        mailer = BeagleSender()
	subject = _(u'A web page you are watching has changed')
        mailer.send(to=[self.recipient['email']],
                    subject=subject, body=self.content)

