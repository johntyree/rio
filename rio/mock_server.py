#!/usr/bin/env python2
# coding: utf8

from __future__ import division, print_function

import itertools
import os
import time

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from .utilities import unicode_dammit, render_dict, by_chunks_of
from .server import show_connection
from .streamer import MetadataInjector

import logging
logger = logging.getLogger(__name__)


ICY_METAINT = 10000

icy_info = [("StreamTitle='{}';".format(s), t) for s, t in [
            (u"AD - 1 AD AD", 1),
            (u"first - second", 4),
            (u"3 AD AD AD", 1),
            (u"third - fourth", 4),
            (u"AD - 4 AD AD AD AD", 1),
            (u"fifth - sixth", 4),
            (u"AD - 5 AD AD AD AD AD", 1)
            ]]


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):

        pretty_headers = unicode_dammit(render_dict(self.headers))
        show_connection(pretty_headers)

        self.send_response(200)
        self.send_header('Content-type', 'audio/mpeg')
        self.send_header('icy-metaint', ICY_METAINT)
        self.end_headers()
        output_buffer = MetadataInjector(self.wfile, ICY_METAINT)
        icy = itertools.cycle(icy_info)
        filename = os.path.join(os.path.dirname(__file__), 'sample.mp3')
        with open(filename, 'r') as f:
            data = itertools.cycle(
                itertools.imap(b''.join, by_chunks_of(1024, f.read())))
            while True:
                start_time = time.time()
                output_buffer.icy, tm = next(icy)
                logger.info("New ICY: {!r}".format(output_buffer.icy))
                while time.time() - start_time < tm:
                    output_buffer.write(next(data))


def serve_on_port(host, port):
    server = HTTPServer((host, port), Handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main():
    """Run main."""

    serve_on_port('localhost', 12345)

    return 0

if __name__ == '__main__':
    main()
