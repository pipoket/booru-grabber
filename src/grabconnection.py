import os
import sys

import socks
import socket

import httplib
import urllib2


class SocksProxyConnection(httplib.HTTPConnection):
    def __init__(self, proxytype, proxyaddr, proxyport=None, rdns=False, username=None, password=None, *args, **kwargs):
        self.proxyargs = (proxytype, proxyaddr, proxyport, rdns, username, password)
        httplib.HTTPConnection.__init__(self, *args, **kwargs)

    def connect(self):
        self.sock = socks.socksocket()
        self.sock.setproxy(*self.proxyargs) 
        if isinstance(self.timeout, float):
            self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))


class SocksProxyHandler(urllib2.HTTPHandler):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kw = kwargs
        urllib2.HTTPHandler.__init__(self)

    def http_open(self, req):
        def build(host, port=None, strict=None, timeout=0):
            conn = SocksProxyConnection(*self.args, host=host, port=port, strict=strict, timeout=timeout, **self.kw)
            return conn
        return self.do_open(build, req)


def get_url_opener(ui):
    ua = ui.get_useragent()
    proxy_info = ui.get_proxy_info()
    if proxy_info:
        socks_handler = SocksProxyHandler(proxy_info["type"], proxy_info["host"], proxy_info["port"])
        opener = urllib2.build_opener(socks_handler)
    else:
        opener = urllib2.build_opener()
    opener.addheaders = [('User-Agent', ua)]
    return opener
