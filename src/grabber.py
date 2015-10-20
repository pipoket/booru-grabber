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
import ConfigParser

import socks
import socket

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
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.71 Safari/537.36"

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
                "Maximum number of active downloads (1-32)")
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

        userAgentSizer = wx.BoxSizer(wx.VERTICAL)
        userAgentLabel = wx.StaticText(self.panel, wx.ID_ANY,
                "User Agent (Leave blank to use default one)")
        self.userAgentText = wx.TextCtrl(self.panel, wx.ID_ANY, DEFAULT_USER_AGENT)
        userAgentSizer.Add(userAgentLabel, 0, wx.BOTTOM, 3)
        userAgentSizer.Add(self.userAgentText, 1, wx.EXPAND)

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

        self.optionBoxSizer = optionBoxSizer
        optionBoxSizer.AddSpacer(5)
        optionBoxSizer.Add(downloadCountSizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        optionBoxSizer.AddSpacer(5)
        optionBoxSizer.Add(downloadPathSizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        optionBoxSizer.AddSpacer(10)
        optionBoxSizer.Add(self.createTagFolder, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        optionBoxSizer.AddSpacer(10)
        optionBoxSizer.Add(self.overwriteFile, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        optionBoxSizer.AddSpacer(10)
        optionBoxSizer.Add(userAgentSizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        optionBoxSizer.AddSpacer(10)
        optionBoxSizer.Add(socksOptionSizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        optionBoxSizer.AddSpacer(10)

        self.downloadCountSizer = downloadCountSizer

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
        self.downloadCount.SetRange(1, 32)

        self.prepareUI()
        self.prepareCores()
        self.prepareOptions()

    def prepareUI(self):
        self.socksRadioBox.Enable(False)
        self.socksTextBox.Enable(False)
        self.stopButton.Enable(False)

    def prepareCores(self):
        self.path = CURRENT_PATH
        self.gd = GrabDownloader(ui=self, path=self.path)

    def prepareOptions(self):
        try:
            config = ConfigParser.SafeConfigParser()
            config.read("config.ini")
            self.downloadCount.SetValue(config.getint("Options", "downloadCount"))
            self.downloadPathText.SetValue(config.get("Options", "downloadPath"))
            self.gd.update_path(self.downloadPathText.GetValue())
            self.createTagFolder.SetValue(config.getboolean("Options", "createTagFolder"))
            self.overwriteFile.SetValue(config.getboolean("Options", "overwriteFile"))
            self.userAgentText.SetValue(config.get("Options", "userAgentText"))
            self.useSocks.SetValue(config.getboolean("Options", "useProxy"))
            if self.useSocks.IsChecked():
                proxyType = config.getint("Options", "proxyType")
                self.socksRadioBox.Enable(True)
                self.socksTextBox.Enable(True)
                if proxyType == socks.HTTP:
                    self.optionHttp.SetValue(True)
                    self.optionSocks4.SetValue(False)
                    self.optionSocks5.SetValue(False)
                elif proxyType == socks.SOCKS4:
                    self.optionHttp.SetValue(False)
                    self.optionSocks4.SetValue(True)
                    self.optionSocks5.SetValue(False)
                elif proxyType == socks.SOCKS5:
                    self.optionHttp.SetValue(False)
                    self.optionSocks4.SetValue(False)
                    self.optionSocks5.SetValue(True)
                self.socksHostText.SetValue(config.get("Options", "proxyHost"))
                self.socksPortText.SetValue(config.get("Options", "proxyPort"))
        except Exception, e:
            self.saveOptions()
            self.updateStatus("Config file not found or parse error. Created new one.")

    def saveOptions(self):
        config = ConfigParser.SafeConfigParser()
        config.add_section("Options")
        config.set("Options", "downloadCount", str(self.downloadCount.GetValue()))
        config.set("Options", "downloadPath", self.downloadPathText.GetValue())
        config.set("Options", "createTagFolder", 'true' if self.createTagFolder.IsChecked() else 'false')
        config.set("Options", "overwriteFile", 'true' if self.overwriteFile.IsChecked() else 'false')
        config.set("Options", "userAgentText", self.userAgentText.GetValue() or DEFAULT_USER_AGENT)
        config.set("Options", "useProxy", 'true' if self.useSocks.IsChecked() else 'false')
        if self.useSocks.IsChecked():
            if self.optionHttp.GetValue():
                proxyType = socks.HTTP
            elif self.optionSocks4.GetValue():
                proxyType = socks.SOCKS4
            elif self.optionSocks5.GetValue():
                proxyType = socks.SOCKS5
            else:
                proxyType = socks.HTTP
            config.set("Options", "proxyType", str(proxyType))
        config.set("Options", "proxyHost", self.socksHostText.GetValue())
        config.set("Options", "proxyPort", str(self.socksPortText.GetValue()))
        with open("config.ini", "w") as config_file:
            config.write(config_file)

    def get_proxy_info(self):
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

    def get_useragent(self):
        ua = self.userAgentText.GetValue().strip()
        if not ua:
            ua = DEFAULT_USER_AGENT
            self.userAgentText.SetValue(DEFAULT_USER_AGENT)
        return ua

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
        self.enableOptionsUI(False)
        self.downloadButton.Enable(False)
        self.searchText.Enable(False)
        self.updateStatus("Begin searching %s... This may take up some time." % value)
        self.gd.update_tags(value)
        self.gd.update_dcount(dvalue)

        gevent.spawn(self.gd.start_download)

    def enableOptionsUI(self, enable=True):
        self.downloadCount.Enable(enable)
        self.downloadPathButton.Enable(enable)
        self.createTagFolder.Enable(enable)
        self.overwriteFile.Enable(enable)
        self.userAgentText.Enable(enable)
        self.useSocks.Enable(enable)
        self.optionHttp.Enable(enable)
        self.optionSocks4.Enable(enable)
        self.optionSocks5.Enable(enable)
        self.socksTextBox.Enable(enable)

    def onStop(self, evt):
        self.gd.stop_download()
        self.stopButton.Enable(False)

    def onExit(self, evt):
        self.Close(True)

    def onTerminate(self, evt):
        self.saveOptions()
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
