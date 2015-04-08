# -*- coding: cp949 -*-
#
# Copyright (C) 2011 by Woosuk Suh
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import re
import sys
import urllib2

from twisted.internet import defer 
from twisted.internet import reactor
from twisted.web.client import getPage 


LIST_URL = "http://gelbooru.com/index.php?page=post&s=list&tags=%(tags)s&pid=%(page_index)s"

LASTPAGE_PATT = re.compile(r'href=".+pid=(.[0-9]+?)" alt="last page">')
IMGSTART_PATT = re.compile(r'<span id="s(.[0-9]+?)" class="thumb">')



class SearchEngine(object):
    def __init__(self, tags="", ui=None):
        self.tags = tags
        self.ui = ui 
        self.codes = set([])
        self.deferreds = []
        self.sema = defer.DeferredSemaphore(256)

    def update_tags(self, tags):
        self.tags = tags

    def fetch_list_page(self, page=0):
        def err_page(reason):
            self.ui.updateError("Error: %s, %s" % (repr(reason), reason.getErrorMessage()))


        url = LIST_URL % {"page_index": page, "tags": self.tags}
        url = url.encode("cp949")

        d = getPage(url, agent="Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20")
        d.addCallback(self.get_codes)
        d.addErrback(err_page)
        self.deferreds.append(d)

    def get_last_page_and_img_per_page(self):
        self.ui.updateStatus("Getting last page...")
        req = urllib2.Request(LIST_URL % {"page_index": 0, "tags": self.tags})
        opener = urllib2.build_opener()
        try:
            result_html = opener.open(req).read()
        except urllib2.URLError:
            self.ui.updateError("Cannot get page information. Please check your internet connection.")
            last_page = None
            return last_page

        if re.findall("Nobody here but us chickens!", result_html):
            self.ui.updateStatus("No result found!")
            last_page = None
        else:
            # First get the count of image per page
            img_per_page = len(re.findall(IMGSTART_PATT, result_html))
            self.ui.updateStatus("Found %d images on each page" % img_per_page)

            try:
                last_pid = re.findall(LASTPAGE_PATT, result_html)[0]
                last_page = int(last_pid)/img_per_page + 1
            except IndexError:
                # There exists only one page.
                last_page = 1
            self.ui.updateStatus("Last page is %s" % last_page)
        return last_page, img_per_page


    def do_search(self, deferred):
        last_page, img_per_page = self.get_last_page_and_img_per_page()
        if not last_page:
            return

        for page in range(0, last_page):
            d = self.sema.run(self.fetch_list_page, page*img_per_page)
            self.deferreds.append(d)
        dl = defer.DeferredList(self.deferreds, consumeErrors=True)
        dl.addCallback(self.got_codes, deferred)

    def get_codes(self, content):
        codes = re.findall(IMGSTART_PATT, content)
        self.codes.update(codes)
        self.ui.updateStatus("%s items found until now." % len(self.codes))

    def got_codes(self, result, d):
        self.ui.updateStatus("Total %s items found" % len(self.codes))
        d.callback(self.codes)
