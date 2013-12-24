#!/usr/bin/env python2
# coding: utf-8
from __future__ import print_function

import itertools
from SocketServer import ForkingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from .streamer import icystream

from .config import HOST, PORT, STREAMS, ICY_METAINT


def print_headers(headers):
    for key, val in headers.items():
        print("{key}: {val}".format(key=key, val=val))


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # FIXME: When the content-type changes between streams, we're probably
        # boned.
        forward = 'icy-metadata' in self.headers
        self.send_response(200)
        self.send_header('Content-type', 'audio/mpeg')
        if forward:
            self.send_header('icy-metaint', str(ICY_METAINT))
        self.end_headers()
        try:
            for url in itertools.cycle(STREAMS):
                icystream(url, self.wfile, forward_metadata=forward)
        except KeyboardInterrupt:
            pass


class ForkingHTTPServer(ForkingMixIn, HTTPServer):
    pass


def serve_on_port(host=HOST, port=PORT):
    server = HTTPServer(("localhost", port), Handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()
