import os
import sys

import socks
import socket

import urllib
import http.client

from urllib.request import HTTPHandler, HTTPSHandler


class SocksProxyHTTPConnection(http.client.HTTPConnection):
    def __init__(self, proxytype, proxyaddr, proxyport=None, rdns=False, username=None, password=None, *args, **kwargs):
        self.proxyargs = (proxytype, proxyaddr, proxyport, rdns, username, password)
        super(SocksProxyHTTPConnection, self).__init__(*args, **kwargs)

    def connect(self):
        self.sock = socks.socksocket()
        self.sock.setproxy(*self.proxyargs) 
        if isinstance(self.timeout, float):
            self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))


class SocksProxyHTTPHandler(HTTPHandler):
    def __init__(self, *args, **kwargs):
        super()
        self.args = args
        self.kw = kwargs
        self._debuglevel = 0

    def http_open(self, req):
        def build(host, port=None, timeout=0):
            conn = SocksProxyHTTPConnection(*self.args, host=host, port=port, timeout=timeout, **self.kw)
            return conn
        return self.do_open(build, req)


class SocksProxyHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, proxytype, proxyaddr, proxyport=None, rdns=False, username=None, password=None, *args, **kwargs):
        self.proxyargs = (proxytype, proxyaddr, proxyport, rdns, username, password)
        super(SocksProxyHTTPSConnection, self).__init__(*args, **kwargs)

    def connect(self):
        self.sock = socks.socksocket()
        self.sock.setproxy(*self.proxyargs) 
        if isinstance(self.timeout, float):
            self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))
        self.sock = self._context.wrap_socket(self.sock,
                                              server_hostname=self.host)


class SocksProxyHTTPSHandler(HTTPSHandler):
    def __init__(self, *args, **kwargs):
        super()
        self.args = args
        self.kw = kwargs
        self._debuglevel = 0

    def https_open(self, req):
        def build(host, port=None, timeout=0):
            conn = SocksProxyHTTPSConnection(*self.args, host=host, port=port, timeout=timeout, **self.kw)
            return conn
        return self.do_open(build, req)


def get_url_opener(ui):
    ua = ui.get_useragent()
    proxy_info = ui.get_proxy_info()
    if proxy_info:
        socks_http_handler = SocksProxyHTTPHandler(proxy_info["type"], proxy_info["host"], proxy_info["port"])
        socks_https_handler = SocksProxyHTTPSHandler(proxy_info["type"], proxy_info["host"], proxy_info["port"])
        opener = urllib.request.build_opener(socks_http_handler, socks_https_handler)
    else:
        opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', ua)]
    return opener
