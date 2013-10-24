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

from scrapy.http import Request
from scrapy.contrib.spidermiddleware.referer import RefererMiddleware

class OriginRefererMiddleware(RefererMiddleware):
    """
    Class that sets the Referer as the original url in case of a redirect of
    the original page. This is needed since users are assigned to the original
    urls and those urls are used in search
    """

    def process_spider_output(self, response, result, spider):
        def _set_referer(r):
            if isinstance(r, Request):
                # Try to get the first redirect_url or default to the
                # response url (which is the response of the previous item
                site = response.request.meta.get('redirect_urls',
                                                 [response.url])[0]
                r.headers.setdefault('Referer', site)
            return r
        return (_set_referer(r) for r in result or ())
