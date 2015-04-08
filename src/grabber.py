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

import wx
import os
import sys
import thread
import urllib

from twisted.internet import wxreactor
wxreactor.install()

from twisted.internet import defer
from twisted.internet import reactor

from searchengine import SearchEngine
from grabdownloader import GrabDownloader



# Helper functions to get current directory within py2exe environment
# Source: http://www.py2exe.org/index.cgi/WhereAmI
def we_are_frozen():
    """Returns whether we are frozen via py2exe.
    This will affect how we find out where we are located."""

    return hasattr(sys, "frozen")


def module_path():
    """ This will get us the program's directory,
    even if we are frozen using py2exe"""

    if we_are_frozen():
        return os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding( )))

    return os.path.dirname(unicode(__file__, sys.getfilesystemencoding( )))


WINDOW_TITLE = "Gelbooru Grabber"
CURRENT_PATH = os.path.abspath(module_path())


class GrabberFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, WINDOW_TITLE, 
                style=wx.DEFAULT_FRAME_STYLE & ~(wx.MAXIMIZE_BOX),
                size=(450, -1))
        self.panel = wx.Panel(self, wx.ID_ANY)

        topLabel = wx.StaticText(self.panel, wx.ID_ANY,
                "Type tags just like you do in Gelbooru. (e.g. 'elf rating:explicit')")
        self.searchText = wx.TextCtrl(self.panel, wx.ID_ANY, "")

        optionBox = wx.StaticBox(self.panel, wx.ID_ANY, "Options")

        downloadCountSizer = wx.BoxSizer(wx.HORIZONTAL)
        downloadCountLabel = wx.StaticText(self.panel, wx.ID_ANY,
                "Maximum number of active downloads (1-256)")
        self.downloadCount = wx.SpinCtrl(self.panel, wx.ID_ANY)
        downloadCountSizer.Add(downloadCountLabel, 0, wx.RIGHT, 15)
        downloadCountSizer.Add(self.downloadCount)

        downloadPathSizer = wx.BoxSizer(wx.VERTICAL)
        downloadPathLabel = wx.StaticText(self.panel, wx.ID_ANY,
                "Save downloaded images to")
        downloadPathTextSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.downloadPathText = wx.TextCtrl(self.panel, wx.ID_ANY, CURRENT_PATH,
                style=wx.TE_READONLY)
        self.downloadPathButton = wx.Button(self.panel, wx.ID_ANY, "Change...")
        self.Bind(wx.EVT_BUTTON, self.onDownloadPath, self.downloadPathButton)
        downloadPathTextSizer.Add(self.downloadPathText, 1, wx.EXPAND | wx.RIGHT, 5)
        downloadPathTextSizer.Add(self.downloadPathButton)
        downloadPathSizer.Add(downloadPathLabel, 0, wx.BOTTOM, 3)
        downloadPathSizer.Add(downloadPathTextSizer, 1, wx.EXPAND)

        createTagFolderSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.createTagFolder = wx.CheckBox(self.panel, wx.ID_ANY,
                style=wx.CHK_2STATE)
        self.createTagFolder.SetValue(True)
        createTagFolderLabel = wx.StaticText(self.panel, wx.ID_ANY,
                "Create a new folder with tagname")
        createTagFolderSizer.Add(self.createTagFolder, 0, wx.RIGHT, 5)
        createTagFolderSizer.Add(createTagFolderLabel, 1)

        overwriteFileSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.overwriteFile = wx.CheckBox(self.panel, wx.ID_ANY,
                style=wx.CHK_2STATE)
        overwriteFileLabel = wx.StaticText(self.panel, wx.ID_ANY,
                "Redownload and overwrite image if it exists already")
        overwriteFileSizer.Add(self.overwriteFile, 0, wx.RIGHT, 5)
        overwriteFileSizer.Add(overwriteFileLabel, 1)

        self.downloadButton = wx.Button(self.panel, wx.ID_ANY, "Download")
        self.exitButton = wx.Button(self.panel, wx.ID_ANY, "Exit")
        self.Bind(wx.EVT_BUTTON, self.onDownload, self.downloadButton)
        self.Bind(wx.EVT_BUTTON, self.onExit, self.exitButton)

        statusLabel = wx.StaticText(self.panel, wx.ID_ANY, "Status displayed below:")
        errorLabel = wx.StaticText(self.panel, wx.ID_ANY, "Errors displayed below:")
        self.statusText = wx.TextCtrl(self.panel, wx.ID_ANY,
                size=(-1, 100),
                style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.errorText = wx.TextCtrl(self.panel, wx.ID_ANY,
                size=(-1, 100),
                style=wx.TE_MULTILINE|wx.TE_READONLY)

        grandSizer = wx.BoxSizer(wx.VERTICAL)
        searchSizer = wx.BoxSizer(wx.HORIZONTAL)
        optionBoxSizer = wx.StaticBoxSizer(optionBox, wx.VERTICAL)
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        statusSizer = wx.BoxSizer(wx.VERTICAL)
       
        searchSizer.Add(self.searchText, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        optionBoxSizer.AddSpacer(5)
        optionBoxSizer.Add(downloadCountSizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        optionBoxSizer.AddSpacer(5)
        optionBoxSizer.Add(downloadPathSizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        optionBoxSizer.AddSpacer(10)
        optionBoxSizer.Add(createTagFolderSizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        optionBoxSizer.AddSpacer(10)
        optionBoxSizer.Add(overwriteFileSizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        optionBoxSizer.AddSpacer(10)

        buttonSizer.Add(self.downloadButton, 0, wx.ALL, 0)
        buttonSizer.Add(self.exitButton, 0, wx.ALL, 0)

        statusSizer.Add(statusLabel, 0, wx.LEFT)
        statusSizer.Add(self.statusText, 0, wx.CENTER|wx.EXPAND)
        statusSizer.Add(errorLabel, 0, wx.LEFT)
        statusSizer.Add(self.errorText, 0, wx.CENTER|wx.EXPAND)

        grandSizer.Add(topLabel, 0, wx.CENTER | wx.ALL, 5)
        grandSizer.Add(searchSizer, 0, wx.EXPAND | wx.ALL, 5)
        grandSizer.AddSpacer(5)
        grandSizer.Add(optionBoxSizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        grandSizer.Add(buttonSizer, 0, wx.CENTER | wx.ALL, 5)
        grandSizer.Add(statusSizer, 0, wx.CENTER | wx.EXPAND | wx.ALL, 5)
        self.panel.SetSizer(grandSizer)
        grandSizer.Fit(self)

        self.downloadCount.SetValue(8)
        self.downloadCount.SetRange(1, 256)

        self.prepareCores()

    def prepareCores(self):
        self.path = CURRENT_PATH
        self.gd = GrabDownloader(ui=self, path=self.path)

    def onDownloadPath(self, evt):
        dlg = wx.DirDialog(self, "Select path to save images",
                style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() == wx.ID_OK:
            self.path = dlg.GetPath()
            self.downloadPathText.SetValue(self.path)
            self.gd.update_path(self.path)
        dlg.Destroy()

    def onDownload(self, evt):
        value = self.searchText.GetValue().strip()
        value = urllib.quote_plus(value)
        if not value:
            self.updateError("Please input the tag value!")
            return
        try:
            dvalue = self.downloadCount.GetValue()
            dvalue = int(dvalue)
        except ValueError:
            self.updateError("Please input correct # of files to download simultaneously!")
            return


        self.downloadButton.Enable(False)
        self.searchText.Enable(False)
        self.updateStatus("Begin searching %s... This may take up some time." % value)
        self.gd.update_tags(value)
        self.gd.update_dcount(dvalue)

        reactor.callLater(0, self.gd.start_download)

    def onExit(self, evt):
        self.Close(True)
        reactor.callLater(0, reactor.stop)

    def updateStatus(self, text):
        self.statusText.WriteText(text)
        self.statusText.WriteText("\n")

    def updateError(self, text):
        self.errorText.WriteText(text)
        self.errorText.WriteText("\n")


if __name__ == "__main__":
    app = wx.PySimpleApp()
    frame = GrabberFrame()
    frame.Show()
    reactor.registerWxApp(app)
    reactor.run()
