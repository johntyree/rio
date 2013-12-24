#!/usr/bin/env python3
# coding: utf-8

from __future__ import print_function

# import cStringIO
import re
import requests
import sys
import time
from math import ceil
from urllib2 import urlparse
urlparse, urljoin = urlparse.urlparse, urlparse.urljoin

from .config import AD_TITLES as bacteria, ICY_METAINT


metadata_regex = re.compile(
    r"StreamTitle='(?P<artist>.*)(?: - )(?P<title>.*?)';")
stream_title = "{artist} - {title}"


def rotten(meat):
    """ Make sure the meat isn't rotting with bact^H^H^H^Hcommercials. """
    if meat:
        for bacterium in bacteria:
            if bacterium in meat or meat in bacterium:
                print("{!r} <-> {!r}!".format(meat, bacterium))
        return any(bacterium in meat or meat in bacterium
                   for bacterium in bacteria)
    else:
        return False


def parse_meat(stream):
    """ Read the metadata out of an IcyCast stream assuming that the
    metadata begins at byte 0.

    Return the metadata if it's ok.
    Return None if it looks like a commercial.

    """
    meatlen = stream.read(1)
    meatlen = ord(meatlen) * 16
    return stream.read(meatlen).strip()


def format_meat(meat):
    match = metadata_regex.search(meat)
    if match:
        return stream_title.format(**match.groupdict())
    else:
        return "Unknown format: {!r}".format(meat)


class BufferedRequest(object):
    """ A buffer for a `requests.request` object, providing a read(size)
    method similar to other buffer IO.

    """
    def __init__(self, req, chunksize=1024*10):
        self.content_iterator = req.iter_content(chunksize)
        self.buf = ''

    def read(self, size):
        while size > len(self.buf):
            # FIXME: Use some kind of sensible fifo
            self.buf += next(self.content_iterator)
        ret, self.buf = self.buf[:size], self.buf[size:]
        return ret


class MetadataInjector(object):
    """ A wrapper around an output buffer that inserts ICY format metadata
    every `metaint` bytes.

    """

    def __init__(self, output_buffer, metaint):
        self.output_buffer = output_buffer
        self.metaint = metaint
        self.remaining = metaint
        self._icy = ""

    def icy():
        doc = "The icy metadata, padded."

        def fget(self):
            return self._icy

        def fset(self, value):
            """ Pad it out to a multiple of 16 bytes """
            icylen = int(ceil(len(value) / 16.0)) * 16
            self._icy = "{value:\x00<{icylen}s}".format(value=value,
                                                        icylen=icylen)
        return locals()
    icy = property(**icy())

    def write(self, data):
        buf = data
        if self.metaint >= 0:
            while len(buf) >= self.remaining:
                data, buf = buf[:self.remaining], buf[self.remaining:]
                self.output_buffer.write(data)
                self.remaining = self.metaint
                self.write_icy()
            self.remaining -= len(buf)
        self.output_buffer.write(buf)

    def write_icy(self):
        if self.icy:
            icylen = chr(len(self.icy) / 16)
            self.output_buffer.write(icylen)
            self.output_buffer.write(self.icy)
            self._icy = ''
        else:
            self.output_buffer.write('\x00')


def print_headers(headers):
    for key, val in headers.items():
        print("{key}: {val}".format(key=key, val=val))


def icystream(url, output_buffer, forward_metadata=False):
    """Stream MP3 data, parsing the titles as you go and givng up when a
    commercial is detected.

    """

    print("Starting:", url)

    elapsed = ''
    fout = sys.stdout

    # Start the request, asking for metadata intervals
    req = requests.get(url, headers={'icy-metadata': 1}, stream=True)
    if not req.ok:
        print("{code}: {reason}".format(code=req.status_code,
                                        reason=req.reason),
              file=fout)
        return
    else:
        print_headers(req.headers)

    try:
        interval = int(req.headers['icy-metaint'])
        output_buffer = MetadataInjector(output_buffer, ICY_METAINT)
    except KeyError as e:
        print(e)
        interval = 0
        output_buffer = MetadataInjector(output_buffer, 0)
    stream = BufferedRequest(req)

    start_time = time.time()
    while True:
        chunk = stream.read(interval)
        raw_meat = parse_meat(stream)
        if raw_meat:
            output_buffer.icy = raw_meat
            meat = format_meat(raw_meat)
            if elapsed:
                print(file=fout)
            fout.write(meat)
            elapsed = ''
            start_time = time.time()
        elif meat is None:
            # Found an ad title in the stream, abort!
            print("Rotten!", file=fout)
            start_time = time.time()
            elapsed = ''
            return
        else:
            print(chr(8) * len(elapsed), end='', file=fout)
            elapsed = " (" + elapsed_since(start_time) + ")"
            print(elapsed, end='', file=fout)
        fout.flush()
        output_buffer.write(chunk)


def elapsed_since(start):
    """ Return a string minutes:seconds of time pased since `start`.

    `start` - Seconds since the epoch.

    """
    data = {'minutes': 0, 'hours': 0, 'days': 0, 'seconds': 0}
    elapsed = int(round(time.time() - start))
    data['minutes'], data['seconds'] = divmod(elapsed, 60)
    template = "{minutes}:{seconds:02d}"
    if data['minutes'] > 60:
        template = "{hours}h {minutes:02d}:{seconds:02d}"
        data['hours'], data['minutes'] = divmod(data['minutes'], 60)
    if data['hours'] > 24:
        template = "{days}d {hours:02d}h {minutes:02d}:{seconds:02d}"
        data['days'], data['hours'] = divmod(data['hours'], 24)
    return template.format(**data)
