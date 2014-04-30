#!/usr/bin/env python2
# coding: utf8

from __future__ import print_function

import itertools as it
from SocketServer import ForkingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from .config import RioConfig
from .utilities import render_headers
from .buffered_request import BufferedRequest
from .icy_tools import IcyData, parse_icy, rebuffer_icy, validate_icy_stream
from .stream_processor import write_stream_to_buf

import logging
logger = logging.getLogger(__name__)


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # FIXME: When the content-type changes between streams, we're probably
        # boned.
        config = RioConfig()

        self.headers['client'] = "{}:{}".format(*self.client_address)
        pretty_headers = render_headers(self.headers.dict)
        show_connection(pretty_headers)

        config.forward_metadata = 'icy-metadata' in self.headers
        self.send_response(200)
        self.send_header('Content-type', 'audio/mpeg')
        if config.forward_metadata:
            self.send_header('icy-metaint', str(config.ICY_METAINT))
        self.end_headers()
        # try:
        for stream in it.islice(config.cycle_streams(), 1):
            stream.data = BufferedRequest(stream.url,
                                          headers={'icy-metadata': 1})
            if not stream.data.ok:
                return
            req = stream.data.req
            # Will we be receiving icy metadata? Forward it.
            upstream_metaint = int(req.headers.get('icy-metaint', None))
            downstream_metaint = config.ICY_METAINT
            if not upstream_metaint:
                logger.warning(u"No metadata recieved from stream."
                               u" Ad detection will not work.")

                def forever():
                    while True:
                        yield IcyData(b'', stream.read(upstream_metaint))
                icy_data_stream = forever()
            else:
                icy_data_stream = parse_icy(stream, upstream_metaint)
                icy_data_stream = rebuffer_icy(icy_data_stream,
                                               downstream_metaint)
                icy_data_stream = validate_icy_stream(icy_data_stream)
                stream0, stream1 = it.tee(icy_data_stream)
            with open('/scratch/rio.mp3', 'wb') as buf_file:
                to_buf = write_stream_to_buf(stream0, buf_file)
                downstream = write_stream_to_buf(stream1, self.wfile)
                list(it.izip(to_buf, downstream))

        # except KeyboardInterrupt:
            # pass


def show_connection(headers):
    msg = u"Client Connected:\n{}".format(headers)
    msg = msg.replace('\n', '\n\t')
    logger.info(msg)


class ForkingHTTPServer(ForkingMixIn, HTTPServer):
    pass


def serve_on_port(host, port):
    server = HTTPServer((host, port), Handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()
