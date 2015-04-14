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

import gevent
from gevent import monkey
monkey.patch_all()

import wx
import os
import sys
import urllib

import socks
import socket

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


class GrabberApp(wx.App):
    def MainLoop(self):
        evtloop = wx.EventLoop()
        wx.EventLoop.SetActive(evtloop)

        # This outer loop determines when to exit the application,
        # for this example we let the main frame reset this flag
        # when it closes.
        if sys.platform == "darwin":
            while self.keepGoing:
                while self.keepGoing and evtloop.Pending():
                    evtloop.Dispatch()
                    gevent.sleep(1.0 / 60)
                self.ProcessIdle()
        else:
            while self.keepGoing:
                while evtloop.Pending():
                    evtloop.Dispatch()
                gevent.sleep(1.0 / 30)
                self.ProcessIdle()

    def OnInit(self):
        self.keepGoing = True
        return True

    def ForceTerminate(self):
        # XXX: Is this method necessary?
        self.keepGoing = False


WINDOW_TITLE = "Gelbooru Grabber"
CURRENT_PATH = os.path.abspath(module_path())


class GrabberFrame(wx.Frame):
    def __init__(self, app):
        self.app = app
        self.original_socket = socket.socket

        wx.Frame.__init__(self, None, wx.ID_ANY, WINDOW_TITLE, 
                style=wx.DEFAULT_FRAME_STYLE & ~(wx.MAXIMIZE_BOX),
                size=(450, -1))
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.Bind(wx.EVT_CLOSE, self.onTerminate, self)

        topLabel = wx.StaticText(self.panel, wx.ID_ANY,
                "Type tags just like you do in Gelbooru. (e.g. 'elf rating:explicit')")
        self.searchText = wx.TextCtrl(self.panel, wx.ID_ANY, "")

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

        self.createTagFolder = wx.CheckBox(self.panel, wx.ID_ANY,
                label="Create a new folder with tagname", style=wx.CHK_2STATE)
        self.createTagFolder.SetValue(True)

        self.overwriteFile = wx.CheckBox(self.panel, wx.ID_ANY,
                label="Redownload and overwrite image if it exists already",
                style=wx.CHK_2STATE)

        ## Proxy UI
        optionBox = wx.StaticBox(self.panel, wx.ID_ANY, "Options")
        self.optionBox = optionBox

        socksOptionBox = wx.StaticBox(self.panel, wx.ID_ANY, "Proxy")
        socksOptionSizer = wx.StaticBoxSizer(socksOptionBox, wx.VERTICAL)
        socksUpperSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.useSocks = wx.CheckBox(self.panel, wx.ID_ANY, label="Use Proxy", style=wx.CHK_2STATE)
        socksUpperSizer.Add(self.useSocks, 0, wx.RIGHT, 5)
        self.Bind(wx.EVT_CHECKBOX, self.onUseSocks, self.useSocks)

        socksDetailSizer = wx.BoxSizer(wx.VERTICAL)

        self.socksRadioBox = wx.StaticBox(self.panel, wx.ID_ANY, label="Type")
        socksRadioSizer = wx.StaticBoxSizer(self.socksRadioBox, wx.HORIZONTAL)
        self.optionHttp = wx.RadioButton(self.socksRadioBox, wx.ID_ANY, label="HTTP")
        self.optionSocks4 = wx.RadioButton(self.socksRadioBox, wx.ID_ANY, label="SOCKS4")
        self.optionSocks5 = wx.RadioButton(self.socksRadioBox, wx.ID_ANY, label="SOCKS5")
        socksRadioSizer.Add(self.optionHttp, 0, wx.BOTTOM, 10)
        socksRadioSizer.AddSpacer(5)
        socksRadioSizer.Add(self.optionSocks4, 0, wx.BOTTOM, 10)
        socksRadioSizer.AddSpacer(5)
        socksRadioSizer.Add(self.optionSocks5, 0, wx.BOTTOM, 10)
        socksDetailSizer.Add(socksRadioSizer, 0, wx.EXPAND | wx.ALIGN_CENTER)

        self.socksTextBox = wx.StaticBox(self.panel, wx.ID_ANY, label="Host/Port")
        socksTextSizer = wx.StaticBoxSizer(self.socksTextBox, wx.HORIZONTAL)
        socksHostSizer = wx.BoxSizer(wx.HORIZONTAL)
        socksHostLabel = wx.StaticText(self.socksTextBox, wx.ID_ANY, "Host")
        self.socksHostText = wx.TextCtrl(self.socksTextBox, wx.ID_ANY)
        socksHostSizer.Add(socksHostLabel)
        socksHostSizer.AddSpacer(2)
        socksHostSizer.Add(self.socksHostText, 0, wx.BOTTOM | wx.EXPAND, 10)
        socksPortSizer = wx.BoxSizer(wx.HORIZONTAL)
        socksPortLabel = wx.StaticText(self.socksTextBox, wx.ID_ANY, "Port")
        self.socksPortText = wx.TextCtrl(self.socksTextBox, wx.ID_ANY)
        socksPortSizer.Add(socksPortLabel)
        socksPortSizer.AddSpacer(2)
        socksPortSizer.Add(self.socksPortText, 0, wx.BOTTOM | wx.EXPAND, 10)
        socksTextSizer.Add(socksHostSizer)
        socksTextSizer.AddSpacer(10)
        socksTextSizer.Add(socksPortSizer)
        socksDetailSizer.Add(socksTextSizer, 0, wx.EXPAND)

        socksOptionSizer.Add(socksUpperSizer)
        socksOptionSizer.AddSpacer(5)
        socksOptionSizer.Add(socksDetailSizer, 0, wx.EXPAND)

        ## Buttons
        self.downloadButton = wx.Button(self.panel, wx.ID_ANY, "Download")
        self.stopButton = wx.Button(self.panel, wx.ID_ANY, "Stop")
        self.exitButton = wx.Button(self.panel, wx.ID_ANY, "Exit")
        self.Bind(wx.EVT_BUTTON, self.onDownload, self.downloadButton)
        self.Bind(wx.EVT_BUTTON, self.onStop, self.stopButton)
        self.Bind(wx.EVT_BUTTON, self.onExit, self.exitButton)

        statusLabel = wx.StaticText(self.panel, wx.ID_ANY, "Status displayed below:")
        errorLabel = wx.StaticText(self.panel, wx.ID_ANY, "Errors displayed below:")
        self.statusText = wx.TextCtrl(self.panel, wx.ID_ANY,
                size=(-1, 100),
                style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.statusLabel = wx.StaticText(self.panel, wx.ID_ANY, "Speed: Not Downloading")
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
        optionBoxSizer.Add(self.createTagFolder, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        optionBoxSizer.AddSpacer(10)
        optionBoxSizer.Add(self.overwriteFile, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        optionBoxSizer.AddSpacer(10)
        optionBoxSizer.Add(socksOptionSizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        optionBoxSizer.AddSpacer(10)

        buttonSizer.Add(self.downloadButton, 0, wx.ALL, 0)
        buttonSizer.AddSpacer(10)
        buttonSizer.Add(self.stopButton, 0, wx.ALL, 0)
        buttonSizer.AddSpacer(10)
        buttonSizer.Add(self.exitButton, 0, wx.ALL, 0)

        statusSizer.Add(statusLabel, 0, wx.LEFT)
        statusSizer.Add(self.statusText, 0, wx.CENTER|wx.EXPAND)
        statusSizer.Add(self.statusLabel, 0)
        statusSizer.AddSpacer(10)
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

        self.prepareUI()
        self.prepareCores()

    def prepareUI(self):
        self.socksRadioBox.Enable(False)
        self.socksTextBox.Enable(False)
        self.stopButton.Enable(False)

    def prepareCores(self):
        self.path = CURRENT_PATH
        self.gd = GrabDownloader(ui=self, path=self.path)

    def get_proxy_addr(self):
        if self.useSocks.IsChecked():
            if self.optionHttp.GetValue():
                socksType = socks.HTTP
            elif self.optionSocks4.GetValue():
                socksType = socks.SOCKS4
            elif self.optionSocks5.GetValue():
                socksType = socks.SOCKS5

            socksHost = self.socksHostText.GetValue()
            socksPort = int(self.socksPortText.GetValue())

            return {"type": socksType, "host": socksHost, "port": socksPort}
        else:
            return None

    def onDownloadPath(self, evt):
        dlg = wx.DirDialog(self, "Select path to save images",
                style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() == wx.ID_OK:
            self.path = dlg.GetPath()
            self.downloadPathText.SetValue(self.path)
            self.gd.update_path(self.path)
        dlg.Destroy()

    def onUseSocks(self, evt):
        self.socksRadioBox.Enable(self.useSocks.IsChecked())
        self.socksTextBox.Enable(self.useSocks.IsChecked())

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

        if self.useSocks.IsChecked():
            socksType = None
            if self.optionHttp.GetValue():
                socksType = "HTTP"
            elif self.optionSocks4.GetValue():
                socksType = "SOCKS4"
            elif self.optionSocks5.GetValue():
                socksType = "SOCKS5"
            else:
                self.updateError("Please select type of SOCKS proxy to use!")
                return

            socksHost = self.socksHostText.GetValue()
            socksPort = self.socksPortText.GetValue()
            if not (socksHost and socksPort):
                self.updateError("Please input host/port of SOCKS proxy to use!")

            self.updateStatus("Using %s proxy at %s:%s..." % (socksType, socksHost, socksPort))

        self.stopButton.Enable(True)
        self.optionBox.Enable(False)
        self.downloadButton.Enable(False)
        self.searchText.Enable(False)
        self.updateStatus("Begin searching %s... This may take up some time." % value)
        self.gd.update_tags(value)
        self.gd.update_dcount(dvalue)

        gevent.spawn(self.gd.start_download)

    def onStop(self, evt):
        self.gd.stop_download()
        self.stopButton.Enable(False)

    def onExit(self, evt):
        self.Close(True)

    def onTerminate(self, evt):
        self.Destroy()
        self.app.ForceTerminate()

    def updateStatus(self, text):
        self.statusText.WriteText(text)
        self.statusText.WriteText("\n")

    def updateError(self, text):
        self.errorText.WriteText(text)
        self.errorText.WriteText("\n")



if __name__ == "__main__":
    app = GrabberApp()
    frame = GrabberFrame(app)
    frame.Show()
    gevent.joinall([gevent.spawn(app.MainLoop)])
