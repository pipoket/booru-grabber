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

import socks
import socket

import xml.etree.ElementTree as et

import gevent
from gevent.pool import Pool

from grabconnection import SocksProxyHandler


LIST_URL = "http://gelbooru.com/index.php?page=dapi&s=post&q=index&tags=%(tags)s&pid=%(page_index)s"

LASTPAGE_PATT = re.compile(r'href=".+pid=(.[0-9]+?)" alt="last page">')
IMGSTART_PATT = re.compile(r'<span id="s(.[0-9]+?)" class="thumb">')



class SearchEngine(object):
    def __init__(self, tags="", ui=None):
        self.tags = tags
        self.ui = ui 
        self.file_url_list = set([])
        self.pool = Pool(16)
        self.original_socket = socket.socket

    def update_tags(self, tags):
        self.tags = tags

    def fetch_list_page(self, page=0):
        try:
            req = urllib2.Request(LIST_URL % {"page_index": page, "tags": self.tags})
            proxy_info = self.ui.get_proxy_addr()
            if proxy_info:
                opener = urllib2.build_opener(SocksProxyHandler(proxy_info["type"], proxy_info["host"], proxy_info["port"]) )
            else:
                opener = urllib2.build_opener()

            result_xml = opener.open(req).read()

            root = et.fromstring(result_xml)
            for post in root.iter("post"):
                self.file_url_list.add(post.attrib["file_url"])
            self.ui.updateStatus("%s items found until now." % len(self.file_url_list))
        except Exception, e:
            self.ui.updateError("Error: %s" % e)

    def get_last_page_and_img_per_page(self):
        self.ui.updateStatus("Getting last page...")

        req = urllib2.Request(LIST_URL % {"page_index": 0, "tags": self.tags})
        proxy_info = self.ui.get_proxy_addr()
        if proxy_info:
            opener = urllib2.build_opener(SocksProxyHandler(proxy_info["type"], proxy_info["host"], proxy_info["port"]) )
        else:
            opener = urllib2.build_opener()

        try:
            result_xml = opener.open(req).read()

            root = et.fromstring(result_xml)
            total_count = int(root.attrib["count"])
            img_per_page = len(root.findall("post"))
            last_page = total_count / img_per_page
            self.ui.updateStatus("Found %d images on each page" % img_per_page)
            self.ui.updateStatus("Last page is %s" % last_page)
            return last_page, img_per_page
        except urllib2.URLError:
            self.ui.updateError("Cannot get page information. Please check your internet connection.")
            last_page = None
            return last_page

    def do_search(self):
        last_page, img_per_page = self.get_last_page_and_img_per_page()
        if not last_page:
            return

        for page in range(0, last_page):
            self.pool.spawn(self.fetch_list_page, page)
        self.pool.join()
        self.ui.updateStatus("Total %s items found" % len(self.file_url_list))
        return self.file_url_list
