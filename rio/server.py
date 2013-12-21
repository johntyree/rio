#!/usr/bin/env python2
# coding: utf-8
from __future__ import print_function

import itertools
from SocketServer import ForkingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from .streamer import icystream

from .config import HOST, PORT, STREAMS


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # FIXME: When the content-type changes between streams, we're probably
        # boned.
        self.send_response(200)
        self.send_header("Content-type", "audio/mpeg")
        self.end_headers()
        try:
            for url in itertools.cycle(STREAMS):
                icystream(url, self.wfile)
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
