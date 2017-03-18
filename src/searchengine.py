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
import urllib

import socket

import xml.etree.ElementTree as et

import gevent
from gevent.pool import Pool

from grabconnection import get_url_opener


class SearchEngine(object):
    def __init__(self, raw_tags="", ui=None):
        self.tags = urllib.parse.quote_plus(raw_tags)
        self.ui = ui 
        self.target_list = list()
        self.pool_id = Pool(1)
        self.pool_image = Pool(16)
        self.original_socket = socket.socket
        self.is_downloading = False
        self.stop_downloading = False

    def update_tags(self, raw_tags):
        self.tags = urllib.parse.quote_plus(raw_tags)

    def run_engine(self):
        raise NotImplementedError()

    def do_search(self):
        self.is_downloading = True
        self.run_engine()
        self.ui.updateStatus("Total %s items found" % len(self.target_list))
        self.is_downloading = False
        self.stop_downloading = False
        return self.target_list

    def stop(self):
        while self.is_downloading:
            self.stop_downloading = True
            gevent.sleep(0.1)


class GelbooruEngine(SearchEngine):
    LIST_URL = "https://gelbooru.com/index.php?page=post&s=list&tags=%(tags)s&pid=%(page_index)s"
    POST_URL = "https://gelbooru.com/index.php?page=post&s=view&id=%(image_id)s"
    URL_SCHEME = "https"
    IMAGE_PER_PAGE = 42

    REGEX_POST_ID = re.compile(r'<span id="s(.[0-9]+?)" class="thumb">')
    REGEX_ORIGINAL_URL = re.compile(r'<a href="(.*?)" target="_blank" style="(?:.*)">Original')
    REGEX_RESIZE_ORIGINAL_URL = re.compile(r'Resize image(?:.*)<a href="(.*?)" onclick="Post.highres')
    REGEX_AD = re.compile(r'You are viewing an advertisement')

    def run_engine(self):
        self.ui.updateStatus("Getting image list...")

        image_set = set(list())
        page = 0
        while (not self.stop_downloading):
            partial_list = self.get_list_with_page(page)
            [image_set.add(x) for x in partial_list]
            if len(partial_list) < self.IMAGE_PER_PAGE:
                break
            page += 1

        for image in image_set:
            if self.stop_downloading:
                break
            self.pool_image.spawn(self.get_original_url, image)
        self.pool_image.join()

    def get_list_with_page(self, page=0):
        url = self.LIST_URL % {"page_index": page * self.IMAGE_PER_PAGE, "tags": self.tags}
        req = urllib.request.Request(url)
        try:
            result_page_raw = get_url_opener(self.ui).open(req).read()
            result_page = result_page_raw.decode('utf-8')
            if re.findall(self.REGEX_AD, result_page):
                self.ui.updateStatus("Advertisement found, retry after 5 sec...")
                gevent.sleep(5)
                return self.get_list_with_page(self, page)
            partial_list = re.findall(self.REGEX_POST_ID, result_page)
            self.ui.updateStatus("Found %d images on page %d" % (len(partial_list), page+1))
            return partial_list
        except urllib.error.URLError:
            self.ui.updateError("Cannot connect to server. Maybe bad internet connection?")
            return list()

    def get_original_url(self, image_id):
        url = self.POST_URL % {"image_id": image_id}
        req = urllib.request.Request(url)
        try:
            result_page_raw = get_url_opener(self.ui).open(req).read()
            result_page = result_page_raw.decode('utf-8')
            if re.findall(self.REGEX_AD, result_page):
                self.ui.updateStatus("Advertisement found, retry after 5 sec...")
                gevent.sleep(5)
                return self.get_original_url(self, image_id)
            try:
                original_url_list = re.findall(self.REGEX_RESIZE_ORIGINAL_URL, result_page)
                if not original_url_list:
                    original_url_list = re.findall(self.REGEX_ORIGINAL_URL, result_page)
                original_url = original_url_list[0]

                parse_result = urllib.parse.urlparse(original_url)
                unparse_args = (self.URL_SCHEME, *parse_result[1:])
                fixed_original_url = urllib.parse.urlunparse(unparse_args)

                target = dict()
                target["referer"] = url
                target["image_url"] = fixed_original_url
                self.target_list.append(target)
            except IndexError:
                self.ui.updateError("Error: Cannot find original image URL of %s" % url)
        except urllib.error.URLError as e:
            self.ui.updateError("Error while fetching original image URL from %s: %s" % (url, e))
