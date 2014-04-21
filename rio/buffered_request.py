#!/usr/bin/env python2
# coding: utf8

from __future__ import division, print_function

import logging
logger = logging.getLogger(__name__)

# A little nod to python3
try:
    from urllib import FancyURLopener
except ImportError:
    from urllib.request import FancyURLopener


class BufferedRequest(object):
    """ A buffer for a file-like object, providing a read(size)
    method similar to other buffer IO.

    """
    def __init__(self, url=None, headers=None, chunksize=1024 * 10):
        self.chunksize = chunksize
        self.buf = bytes()
        if url:
            self.get(url, headers)

    def get(self, url, headers=None):
        o = FancyURLopener()
        if headers:
            for k, v in headers.items():
                o.addheader(k, v)
        logger.debug('opening url {!r}'.format(url))
        self.req = o.open(url)
        if not self.ok:
            logger.warning(
                "stream returned HTTP code {}".format(self.req.code))
        if not self.req.headers:
            logger.debug('no headers received')
            self.req.headers = self.build_headers(self)
        return self

    def _build_headers():
        """ Read the stream until the first blank line, building up a header
        dictionary.

        """
        logger.debug("searching for headers in stream")
        hdrs = {}
        data = self.read(4096)
        while True:
            line, _, data = data.partition(b'\r\n')
            if not line:
                # line is only empty on blank line, so we're done
                logger.debug("end of headers")
                buf.appendleft(data)
                break
            elif b':' in line:
                key, _, val = line.partition(b':')
                logger.debug("found header {!r} = {!r}".format(key, val))
                hdrs[key] = val
            else:
                logger.warning("non header line in headers {!r}".format(line))
        return hdrs

    @property
    def ok(self):
        return 200 <= self.req.code < 300

    def read(self, size):
        while size > len(self.buf):
            # FIXME: Use some kind of sensible fifo
            bites = self.req.read(self.chunksize)
            self.buf += bites
            logger.debug("received {} bytes [buflen {}]".format(len(bites),
                                                                len(self.buf)))
        ret, self.buf = self.buf[:size], self.buf[size:]
        logger.debug("produced {} bytes [buflen {}]".format(len(ret),
                                                            len(self.buf)))
        return ret

    def pushback(self, data):
        self.buf = data + self.buf
        return self

    def peek(self, size):
        """ Return the first size bytes of the stream without removal.

        >>> a = buf.peek(10)
        >>> b = buf.read(10)
        >>> assert a == b  # succeeds
        """
        val = self.read(size)
        self.pushback(val)
        return val
