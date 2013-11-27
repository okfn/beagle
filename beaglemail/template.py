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
from jinja2 import Environment, PackageLoader
from scrapy.settings import CrawlerSettings
import beagleboy.settings

def render(path, params={}, locale=None, html=False):
    """
    Render a template with parameters but get the owner from the beagleboy
    settings file (can be overwritten)
    """

    # Load the template from the emails environment of beagle
    env = Environment(loader=PackageLoader('beaglemail', 'templates'),
                      extensions=['jinja2.ext.i18n'])

    # If locale has been provided we install the translation
    if locale:
        translation = gettext.translation('beagle', 'locale',
                                          languages=[locale])
        env.install_gettext_translations(translation)

    # Get the template from the path
    template = env.get_template(path)

    # Render the plain content version
    plain_content = template.render(params)
    # If html is set we add (overwrite) the output parameter with 'html'
    # and generate the html version. Return a tuple of both
    if html:
        params['output'] = 'html'
        return (plain_content, template.render(params))

    # If we get here we just return the plain content
    return plain_content
