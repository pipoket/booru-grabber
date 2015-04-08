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
import os

from twisted.internet import defer 
from twisted.internet import reactor
from twisted.web.client import getPage 

from searchengine import SearchEngine


POST_URL = "http://gelbooru.com/index.php?page=post&s=view&id=%(pid)s"

ORIGINALIMG_PATT = re.compile(r'<a href=\"(.[^#\"]+?)\".+?>Original image</a>')



class GrabDownloader(object):
    def __init__(self, tags="", ui=None, path=None):
        self.tags = tags
        self.path = path
        self.fullpath = None
        self.ui = ui
        self.codes = set([])
        self.deferreds = []
        self.downloaded = 0
        self.sema = None

    def update_tags(self, tags):
        self.tags = tags

    def update_dcount(self, dvalue):
        self.sema = defer.DeferredSemaphore(dvalue)

    def update_path(self, path):
        self.path = path

    def error(self, reason):
        self.ui.updateError("Error: %s, %s" % (repr(reason), reason.getErrorMessage()))

    def start_download(self):
        self.downloaded = 0
        self.se = SearchEngine(self.tags, self.ui)
        d = defer.Deferred()
        d.addCallback(self.download)
        self.se.do_search(d)

    def download(self, codes):
        if self.ui.createTagFolder.IsChecked():
            self.fullpath = os.path.join(self.path, self.tags)
        else:
            self.fullpath = self.path

        self.codes = codes
        try:
            os.mkdir(self.fullpath)
        except OSError:
            self.ui.updateStatus("%s directory already exists!" % self.tags)

        for code in self.codes:
            d = self.sema.run(self._download, code)
            self.deferreds.append(d)
        dl = defer.DeferredList(self.deferreds, consumeErrors=True)
        dl.addCallback(self.download_done)

    def _download(self, code):
        url = POST_URL % {"pid": code}
        d = getPage(url)
        d.addCallback(self.got_post)
        d.addErrback(self.error)
        return d

    def got_post(self, postpage):
        img_url = re.findall(ORIGINALIMG_PATT, postpage)
        if img_url: img_url = img_url[0]
        else: return

        fname = img_url.split("/")[-1]

        if os.path.exists(os.path.join(self.fullpath, fname)) \
                and (not self.ui.overwriteFile.IsChecked()):
            # We don't have to download the existing file again
            # if user does not want to.
            self.downloaded += 1
            self.ui.updateStatus("Progress %s/%s (%.2f %%) - SKIP! (Already downloaded)" % (
                self.downloaded, len(self.codes),
                self.downloaded * 100.0 / len(self.codes)))
            return
        d = getPage(img_url)
        d.addCallback(self.got_img, fname)
        d.addErrback(self.error)
        return d

    def got_img(self, imgfile, fname):
        fp = open(os.path.join(self.fullpath, fname), "wb")
        fp.write(imgfile)
        fp.close()
        self.downloaded += 1
        self.ui.updateStatus("Progress: %s/%s (%.2f %%)" % (self.downloaded, len(self.codes),
                self.downloaded * 100.0 / len(self.codes)))

    def download_done(self, result):
        self.deferreds = []
        self.se = None
        self.ui.updateStatus("Download completed")
        self.ui.downloadButton.Enable(True)
        self.ui.searchText.Enable(True)
