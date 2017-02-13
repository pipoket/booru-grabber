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
import urllib

from io import BytesIO

import gevent
from gevent.pool import Pool

from searchengine import *

from grabconnection import get_url_opener


class GrabDownloader(object):
    def __init__(self, tags="", ui=None, path=None):
        self.tags = tags
        self.path = path
        self.fullpath = None
        self.ui = ui
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
            if elapsed_time > 0:
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

        self.se = GelbooruEngine(self.tags, self.ui)
        target_list = self.se.do_search()

        self.last_elapsed_time = time.time()
        self.ui_updater = gevent.spawn(self.update_speedmeter)
        self.ui.statusLabel.SetLabel("Speed: Estimating...")
        self.ui.statusLabel.Fit()

        self.download(target_list)

    def stop_download(self):
        if self.is_downloading:
            self.is_downloading = False
            self.pool.kill()
            self.pool.join()
            self.se.stop()
            self.se = None
            self.ui.updateStatus("Finishing Download...")

            self.se = None
            self.ui.updateStatus("Download Done")
            self.ui.downloadButton.Enable(True)
            self.ui.stopButton.Enable(False)
            self.ui.searchText.Enable(True)
            self.ui.enableOptionsUI(True)
            if self.ui_updater:
                self.ui_updater.kill()
                self.ui_updater = None
                self.ui.statusLabel.SetLabel("Speed: Not Downloading")
            self.is_downloading = False

    def download(self, target_list):
        if self.ui.createTagFolder.IsChecked():
            valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
            cleaned_tags = self.tags.replace("+", "_")
            cleaned_tags = "".join([x for x in cleaned_tags if x in valid_chars])
            self.fullpath = os.path.join(self.path, cleaned_tags)
        else:
            self.fullpath = self.path

        try:
            os.mkdir(self.fullpath)
        except OSError:
            self.ui.updateStatus("%s directory already exists!" % self.tags)

        total_count = len(target_list)
        for target in target_list:
            self.pool.spawn(self.get_image, target, total_count)
            if not self.is_downloading:
                break
        self.pool.join()
        self.stop_download()

    def get_image(self, target, total_count):
        image_referer = target["referer"]
        image_url = target["image_url"]
        fname = image_url.split("/")[-1]

        if os.path.exists(os.path.join(self.fullpath, fname)) \
                and (not self.ui.overwriteFile.IsChecked()):
            # We don't have to download the existing file again
            # if user does not want to.
            self.downloaded += 1
            self.ui.updateStatus("Progress %s/%s (%.2f %%) - SKIP! (Already downloaded)" % (
                self.downloaded, total_count,
                self.downloaded * 100.0 / total_count))
            return

        req = urllib.request.Request(image_url)
        req.add_header("referer", image_referer)
        try:
            response = get_url_opener(self.ui).open(req)
            img_file_buffer = BytesIO()
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
            self.ui.updateStatus("Progress: %s/%s (%.2f %%)" % (
                self.downloaded, total_count,
                self.downloaded * 100.0 / total_count)
            )
        except urllib.error.HTTPError as ue:
            if ue.code == 503:
                # Temporarily Unavailable Error: Retry!
                self.pool.spawn(self.get_image, image_url, total_count)
            else:
                self.ui.updateError("Error: %s" % ue)
        except Exception as e:
            self.ui.updateError("Error: %s, %s" % (e, image_referer))
