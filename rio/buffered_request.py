#!/usr/bin/env python2
# coding: utf8

from __future__ import division, print_function

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
        self.req = o.open(url)
        return self

    @property
    def ok(self):
        return 200 <= self.req.code < 300

    def read(self, size):
        while size > len(self.buf):
            # FIXME: Use some kind of sensible fifo
            self.buf += self.req.read(self.chunksize)
        ret, self.buf = self.buf[:size], self.buf[size:]
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
