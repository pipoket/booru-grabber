# -*- coding: cp949 -*-
#
# Copyright (C) 2015 by Woosuk Suh
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
import time
import string
import urllib2

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

import gevent
from gevent.pool import Pool

from searchengine import SearchEngine

from grabconnection import SocksProxyHandler


class GrabDownloader(object):
    def __init__(self, tags="", ui=None, path=None):
        self.tags = tags
        self.path = path
        self.fullpath = None
        self.ui = ui
        self.file_urls = set([])
        self.downloaded = 0
        self.pool = None
        self.is_downloading = False

        self.ui_updater = None
        self.total_rx_bytes = 0
        self.last_rx_bytes = 0
        self.total_elapsed_time = 0
        self.last_elapsed_time = 0

    def update_tags(self, tags):
        self.tags = tags

    def update_dcount(self, dvalue):
        self.pool = Pool(dvalue)

    def update_path(self, path):
        self.path = path

    def error(self, reason):
        self.ui.updateError("Error: %s, %s" % (repr(reason), reason.getErrorMessage()))

    def get_speedmeter_string(self, speed):
        meter_KB = 1024
        meter_MB = meter_KB * 1024
        meter_GB = meter_MB * 1024
        meter_TB = meter_GB * 1024

        if speed > meter_TB:
            return "%s TB/sec" % round(speed / meter_TB, 2)
        elif speed > meter_GB:
            return "%s GB/sec" % round(speed / meter_GB, 2)
        elif speed > meter_MB:
            return "%s MB/sec" % round(speed / meter_MB, 2)
        elif speed > meter_KB:
            return "%s KB/sec" % round(speed / meter_KB, 2)
        else:
            return "%s Bytes/sec" % round(speed)

    def update_speedmeter(self):
        while True:
            now_time = time.time()
            elapsed_time = now_time - self.last_elapsed_time
            rx_bytes_per_sec = (self.total_rx_bytes - self.last_rx_bytes) / elapsed_time
            self.last_rx_bytes = self.total_rx_bytes
            self.last_elapsed_time = now_time
            self.total_elapsed_time += elapsed_time
            self.ui.statusLabel.SetLabel("Speed: %s (Elapsed %s secs)" % (
                self.get_speedmeter_string(rx_bytes_per_sec), int(self.total_elapsed_time)))
            gevent.sleep(1)

    def start_download(self):
        self.downloaded = 0
        self.total_rx_bytes = 0
        self.last_rx_bytes = 0
        self.total_elapsed_time = 0
        self.is_downloading = True

        self.se = SearchEngine(self.tags, self.ui)
        file_urls = self.se.do_search()

        self.last_elapsed_time = time.time()
        self.ui_updater = gevent.spawn(self.update_speedmeter)
        self.ui.statusLabel.SetLabel("Speed: Estimating...")
        self.ui.statusLabel.Fit()

        self.download(file_urls)

    def stop_download(self):
        if self.is_downloading:
            self.is_downloading = False
            self.pool.kill()
            self.ui.updateStatus("Cancelling Download...")

    def download(self, file_urls):
        if self.ui.createTagFolder.IsChecked():
            valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
            cleaned_tags = "".join([x for x in self.tags if x in valid_chars])
            self.fullpath = os.path.join(self.path, cleaned_tags)
        else:
            self.fullpath = self.path

        self.file_urls = file_urls
        try:
            os.mkdir(self.fullpath)
        except OSError:
            self.ui.updateStatus("%s directory already exists!" % self.tags)

        for file_url in self.file_urls:
            self.pool.spawn(self.get_image, file_url)
            if not self.is_downloading:
                break
        self.pool.join()

        self.se = None
        self.ui.updateStatus("Download Done")
        self.ui.downloadButton.Enable(True)
        self.ui.searchText.Enable(True)
        self.ui.optionBox.Enable(True)
        if self.ui_updater:
            self.ui_updater.kill()
            self.ui_updater = None
            self.ui.statusLabel.SetLabel("Speed: Not Downloading")
        self.is_downloading = False

    def get_image(self, file_url):
        fname = file_url.split("/")[-1]

        if os.path.exists(os.path.join(self.fullpath, fname)) \
                and (not self.ui.overwriteFile.IsChecked()):
            # We don't have to download the existing file again
            # if user does not want to.
            self.downloaded += 1
            self.ui.updateStatus("Progress %s/%s (%.2f %%) - SKIP! (Already downloaded)" % (
                self.downloaded, len(self.file_urls),
                self.downloaded * 100.0 / len(self.file_urls)))
            return

        req = urllib2.Request(file_url)
        proxy_info = self.ui.get_proxy_addr()
        if proxy_info:
            opener = urllib2.build_opener(SocksProxyHandler(proxy_info["type"], proxy_info["host"], proxy_info["port"]) )
        else:
            opener = urllib2.build_opener()

        try:
            response = opener.open(req)
            img_file_buffer = StringIO.StringIO()
            while True:
                chunk = response.read(16384)
                if not chunk:
                    break
                img_file_buffer.write(chunk)
                self.total_rx_bytes += len(chunk)

            fp = open(os.path.join(self.fullpath, fname), "wb")
            fp.write(img_file_buffer.getvalue())
            fp.close()
            self.downloaded += 1
            self.ui.updateStatus("Progress: %s/%s (%.2f %%)" % (self.downloaded, len(self.file_urls),
                    self.downloaded * 100.0 / len(self.file_urls)))
        except urllib2.URLError, ue:
            if ue.code == 503:
                # Temporarily Unavailable Error: Retry!
                self.pool.spawn(self.get_image, file_url)
            self.ui.updateError("Error: %s" % ue)
        except Exception, e:
            self.ui.updateError("Error: %s" % e)
