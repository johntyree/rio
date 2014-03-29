#!/usr/bin/env python2
# coding: utf8

from __future__ import division, print_function

import itertools
import os
import sys
import time

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from .utilities import unicode_dammit, render_dict
from .streamer import MetadataInjector

ICY_METAINT = 10000


def by_chunks_of(sz, tail):
    while tail:
        head, tail = tail[:sz], tail[sz:]
        yield head


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        pretty_headers = unicode_dammit(render_dict(self.headers))
        print(u"\n{}\n".format(pretty_headers), file=sys.stderr)
        self.send_response(200)
        self.send_header('Content-type', 'audio/mpeg')
        self.send_header('icy-metaint', ICY_METAINT)
        self.end_headers()
        output_buffer = MetadataInjector(self.wfile, ICY_METAINT)
        icy = itertools.cycle((
            (u"StreamTitle='AD - 2 AD AD';", 2),
            (u"StreamTitle='first - second';", 10),
            (u"StreamTitle='3 AD AD AD';", 2),
            (u"StreamTitle='third - fourth';", 10),
            (u"StreamTitle='AD - 4 AD AD AD AD';", 2),
            (u"StreamTitle='fifth - sixth';", 10),
            (u"StreamTitle='AD - 5 AD AD AD AD AD';", 2)
        ))
        filename = os.path.join(os.path.dirname(__file__), 'sample.mp3')
        with open(filename, 'r') as f:
            data = itertools.cycle(by_chunks_of(50, f.read()))
            while True:
                start_time = time.time()
                output_buffer.icy, tm = next(icy)
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
