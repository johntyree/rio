#!/usr/bin/env python2
# coding: utf8

from __future__ import print_function

import itertools as it
import weakref
from collections import defaultdict
from operator import itemgetter
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from .config import RioConfig
from .utilities import render_headers, iflatten, consume, ClonableIterator
from .buffered_request import BufferedRequest
from .icy_tools import parse_icy, rebuffer_icy, takewhile_tags
from .stream_processor import write_stream_to_buf, regex_matches

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

_stream_manager = None


def get_stream_manager():
    logger.debug("grabbing global StreamManager")
    global _stream_manager
    if not _stream_manager:
        logger.debug("creating global StreamManager")
        _stream_manager = StreamManager(genre_stream)
        logger.debug("global StreamManager created")
    return _stream_manager


def genre_stream(genre):
    logger.debug("creating stream for genre {!r}".format(genre))
    config = RioConfig()
    streams = config.streams_in_genre(genre)
    logger.debug("found upstreams {!r} for genre {!r}".format(streams, genre))
    for stream in it.cycle(streams):
        logger.debug("found upstream {!r}".format(stream))
        if stream.data:
            # In theory we don't need to do this, but we probably should.
            stream.data.req.close()
        stream.data = BufferedRequest(
            stream.url, headers={'icy-metadata': 1})
        if not stream.data.ok:
            logger.debug("connection failed {!r}".format(stream))
            continue
        logger.debug("connection established {!r}".format(stream))
        req = stream.data.req
        upstream_metaint = int(req.headers.get('icy-metaint', 0))
        regexen = config.bacteria_for_stream(stream)
        icy_data_stream = parse_icy(stream, upstream_metaint)
        regex_match_stream = regex_matches(icy_data_stream, regexen)
        icy_data_stream = (
            takewhile_tags(lambda s: s != 'AD', regex_match_stream))
        yield rebuffer_icy(icy_data_stream, config.ICY_METAINT)


class StreamManager(object):

    """A proxy class for unifying multiple client connections to a single
    upstream data source."""

    def __init__(self, stream_factory):
        logger.debug("begin StreamManager __init__")
        self.stream_factory = stream_factory
        self.config = RioConfig()
        # FIXME: this grows unbounded in its keys
        self._active_upstreams = {}
        self.subscribers = defaultdict(weakref.WeakSet)
        logger.debug("end StreamManager __init__")

    def grab_upstream(self, genre):
        logger.debug("Grabbing upstream for {!r}".format(genre))
        if genre not in self._active_upstreams:
            logger.debug("{!r} not found, establishing".format(genre))
            container = ClonableIterator(iflatten(self.stream_factory(genre)))
            self._active_upstreams[genre] = container
        return self._active_upstreams[genre]

    def set_upstream(self, genre, val):
        self._active_upstreams[genre] = val

    def connect(self, genre):
        logger.debug("begin StreamManager connect")
        try:
            orig_stream = self.subscribers[genre].pop()
            logger.debug("genre found, grabbed client stream")
        except KeyError:
            logger.debug("genre not found")
            orig_stream = self.grab_upstream(genre)
        logger.debug("cloning stream")
        new_stream = orig_stream.clone()
        logger.debug("stream cloned")
        self.subscribers[genre].add(new_stream)
        logger.debug("stream added to subscriber list for genre")
        return new_stream


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        logger.debug("client connection begin")
        StreamHandler(self).run()
        logger.debug("client connection end")


class StreamHandler(object):

    def __init__(self, request):
        self.stream_manager = get_stream_manager()
        self.request = request

    def init_config(self):
        self.config = RioConfig()
        self.config.forward_metadata = 'icy-metadata' in self.request.headers
        try:
            self.genre = self.request.path.rstrip('/').split('/')[1]
        except:
            self.genre = self.config._opts.genre

    def log_connection(self):
        req = self.request
        req.headers['client'] = "{}:{}".format(*req.client_address)
        req.headers['genre'] = self.genre
        pretty_headers = render_headers(req.headers.dict)
        show_connection(pretty_headers)

    def send_headers(self):
        req = self.request
        req.send_response(200)
        req.send_header('Content-type', 'audio/mpeg')
        if self.config.forward_metadata:
            req.send_header('icy-metaint', str(self.config.ICY_METAINT))
        req.end_headers()

    def run(self):
        # FIXME: When the content-type changes between streams, we're probably
        # boned.
        self.init_config()
        logger.debug("config init finished")
        self.send_headers()
        self.log_connection()
        logger.debug("client connection logged")
        icy_data_stream = self.stream_manager.connect(self.genre)
        logger.debug("upstream connection established")
        consume(write_stream_to_buf(icy_data_stream, self.request.wfile))
        logger.debug("buffer writing complete")


def show_connection(headers):
    msg = u"\tClient Connected:\n{}".format(headers)
    msg = msg.replace('\n', '\n\t\t')
    logger.info('\n' + msg)


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass


def serve_on_port(host, port):
    server = HTTPServer((host, port), Handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()
