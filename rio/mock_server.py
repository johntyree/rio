#!/usr/bin/env python2
# coding: utf8

from __future__ import division, print_function

import itertools
import os

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from .utilities import unicode_dammit, render_dict
from .server import show_connection
from .icy_tools import format_icy

import logging
logger = logging.getLogger(__name__)


ICY_METAINT = 8192

icy_info = [("StreamTitle='{}';".format(s), t) for s, t in [
            (u"AD - 1 AD AD", 1),
            (u"first - second", 4),
            (u"3 AD AD AD", 1),
            (u"third - fourth", 4),
            (u"AD - 4 AD AD AD AD", 1),
            (u"fifth - sixth", 4),
            (u"AD - 5 AD AD AD AD AD", 1)
            ]]


def forever_file(f):
    with open(f, 'rb') as f:
        f = itertools.cycle(f.read())
        while True:
            yield ''.join(itertools.islice(f, ICY_METAINT))


def generate_mock_stream(filename, icy_info):
    stream = forever_file(filename)
    for streamtitle, secs in itertools.cycle(icy_info):
        icy = format_icy(streamtitle)
        logger.info("New ICY: {!r}".format(icy))
        yield next(stream) + icy
        for i in range(t * 20):
            yield next(stream) + b'\x00'


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):

        pretty_headers = unicode_dammit(render_dict(self.headers))
        show_connection(pretty_headers)

        self.send_response(200)
        self.send_header('Content-type', 'audio/mpeg')
        self.send_header('icy-metaint', ICY_METAINT)
        self.end_headers()
        filename = os.path.join(os.path.dirname(__file__), 'sample.mp3')
        stream = generate_mock_stream(filename, icy_info)
        while True:
            self.wfile.write(next(stream))


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
