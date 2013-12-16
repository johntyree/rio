#!/usr/bin/env python2
# coding: utf-8
from __future__ import print_function

from threading import Thread
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import itertools

from simply import icystream, streams

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "audio/mpeg")
        self.end_headers()
        for url in itertools.cycle(streams):
            try:
                icystream(url, self.wfile)
            except:
                print(e)
                return

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass

def serve_on_port(port):
    server = ThreadingHTTPServer(("localhost", port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


serve_on_port(2222)
