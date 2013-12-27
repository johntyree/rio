#!/usr/bin/env python2
# coding: utf8

from __future__ import print_function

import os
import re
import sys
import time
import urllib2
urlparse, urljoin = urllib2.urlparse.urlparse, urllib2.urlparse.urljoin
from math import ceil

import requests

from .utilities import elapsed_since, render_headers, unicode_damnit
from .config import RioConfig

metadata_regex = re.compile(
    ur"StreamTitle='(?P<artist>.*)(?: - )(?P<title>.*?)';")
stream_title = u"{artist} - {title}"


def rotten(meat, bacteria):
    """ Make sure the meat isn't rotting with bact^H^H^H^Hcommercials. """
    return tuple(bacterium.pattern for bacterium in bacteria
                 if bacterium.search(meat))


def show_rotten(raw, bad, file=sys.stderr):
    for b in bad:
        msg = '''Rotten! {!r} <-> {!r}!'''.format(raw, b)
        print(msg, file=file)


def parse_meat(stream):
    """ Read the metadata out of an IcyCast stream assuming that the
    metadata begins at byte 0.

    """
    meatlen = stream.read(1)
    meatlen = ord(meatlen) * 16
    return unicode_damnit(stream.read(meatlen).strip())


def format_meat(meat):
    meat = meat.decode('utf8')
    match = metadata_regex.search(meat)
    if match:
        return stream_title.format(**match.groupdict())
    else:
        return u"Unknown format: {!r}".format(meat)


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

    def appendleft(self, data):
        self.buf = data + self.buf

    def peek(self, size):
        """ Return the first size bytes of the stream without removal.

        a = buf.peek(10)
        b = buf.read(10)
        assert a == b  # succeeds
        """
        val = self.read(size)
        self.appendleft(val)
        return val


class MetadataInjector(object):
    """ A wrapper around an output buffer that inserts ICY format metadata
    every `metaint` bytes.

    """

    def __init__(self, output_buffer, metaint):
        self.output_buffer = output_buffer
        self.metaint = self._bytes_remaining = metaint
        self._icy = ""
        self._last_icy = ""
        self._current_icy = ""

    def __del__(self):
        # Make sure we leave the client stream at the beginning of a chunk to
        # avoid going out of sync when the next incoming stream starts.
        if self._bytes_remaining:
            self.flush()

    def icy():
        doc = "The icy metadata, aligned to 16 bytes."

        def fget(self):
            return self._icy

        def fset(self, value):
            # Convert to utf8
            value = unicode_damnit(value).encode('utf8')
            # Pad it out to a multiple of 16 bytes
            icylen = int(ceil(len(value) / 16.0)) * 16
            self._last_icy = self._current_icy
            self._icy = "{value:\x00<{icylen}s}".format(value=value,
                                                        icylen=icylen)
        return locals()
    icy = property(**icy())

    @property
    def last_icy(self):
        return self._last_icy

    def write(self, buf):
        # If we have metadata to forward
        if self.metaint >= 0:
            # If the buf len is large enough that we'll need to inject, write
            # out as much as needed, then inject
            while len(buf) >= self._bytes_remaining:
                idx = self._bytes_remaining
                data, buf = buf[:idx], buf[idx:]
                self.output_buffer.write(data)
                self._bytes_remaining = self.metaint
                self.write_icy()
            self._bytes_remaining -= len(buf)
        # Here, we'll have between 0 and metaint - 1 left to write so it's safe
        # to push it all out. If there's no metadata, it's always safe.
        self.output_buffer.write(buf)

    def flush(self):
        self.output_buffer.write('\x00' * self._bytes_remaining)
        self.write_icy()
        self._bytes_remaining = self.metaint

    def write_icy(self):
        if self.icy:
            # First tell how long it will be in multiples of 16 bytes
            icylen = chr(len(self.icy) / 16)
            self.output_buffer.write(icylen)
            # Then write it out
            self.output_buffer.write(self.icy)
            # Erase the metadata to avoid constantly rebroadcasting. We'll
            # reset it when we get an update from upstream.
            self._last_icy = self._current_icy
            self._current_icy = self._icy
            self._icy = ""
        elif self.metaint:
            # If no metadata, but they're expecting some, push out a NULL byte
            self.output_buffer.write('\x00')


def build_headers(buf):
    """ Read the stream until the first blank line, building up a header
    dictionary.

    """
    hdrs = requests.structures.CaseInsensitiveDict()
    data = buf.read(4096)
    while True:
        line, _, data = data.partition('\r\n')
        if not line:
            buf.appendleft(data)
            break
        elif ':' in line:
            key, _, val = line.partition(':')
            hdrs[key] = val
    return hdrs


# FIXME: This function is getting seriously crufty...
def icystream(stream, output_buffer, config=None):
    """Stream MP3 data, parsing the titles as you go and givng up when a
    commercial is detected.

    """

    config = config or RioConfig()

    print("Starting {!s}".format(stream))

    elapsed = ''
    fout = sys.stdout

    # Start the request, asking for metadata intervals
    req = requests.get(stream.url, headers={'icy-metadata': 1}, stream=True)
    if not req.ok:
        print("{}: {}".format(req.status_code, req.reason), file=fout)
        return

    # Buffer the input stream
    stream.data = BufferedRequest(req)

    # If we got no headers back, assume that they are in-line. Everything
    # before the blank line is header, everything after is data
    if not req.headers:
        hdrs = build_headers(stream.data)
        req.headers = hdrs

    # Will we be receiving icy metadata? Forward it.
    interval = int(req.headers.get('icy-metaint', 0))
    if interval and config.forward_metadata:
        output_buffer = MetadataInjector(output_buffer, config.ICY_METAINT)
    else:
        output_buffer = MetadataInjector(output_buffer, 0)
    if not interval:
        print(u"No metadata recieved from stream."
              u" Ad detection will not work.", file=fout)

    start_time = time.time()

    print(render_headers(req.headers))
    print(u"Networks: {!r}".format(stream.networks))
    bacteria = config.bacteria_for_stream(stream)
    print(u"Ad Sentinels: {!r}".format([b.pattern for b in bacteria]))

    save_file = None

    OUTPUT_DIR = config.output_directory

    while True:
        updated = config.update()
        chunk = stream.read(interval)
        raw_meat = parse_meat(stream)
        if updated:
            bacteria = config.bacteria_for_stream(stream)
            print(u"\nAd Sentinels: {!r}".format(
                [b.pattern for b in bacteria]), file=fout)
            print(format_meat(output_buffer._current_icy), end='', file=fout)
            elapsed = ''

        # Save the config if it has been updated
        if config.config_age < config.age:
            config.write_config()
        if raw_meat:
            # We got some new metadata

            # If this song is complete but very short, it's
            # probably a commercial
            end_time = time.time()
            min_ad = config.min_ad_length
            max_ad = config.max_ad_length
            new_commercial = all((
                min_ad <= end_time - start_time <= max_ad,
                output_buffer._last_icy
            ))
            if new_commercial:
                if elapsed:
                    print('', file=fout)
                config.add_bacterium(stream.networks,
                                     format_meat(output_buffer._current_icy))

            bad_meat = rotten(raw_meat, bacteria)
            if bad_meat:
                # Found an ad title in the stream, abort!
                print(file=fout)
                show_rotten(raw_meat, bad_meat, file=fout)
                print(file=fout)

                elapsed = ''
                if save_file:
                    save_file.close()

                return
            else:
                # Copy new icy metadata to clients
                output_buffer.icy = raw_meat
                # Put new metadata on a new line
                meat = format_meat(output_buffer.icy)
                if elapsed:
                    print(file=fout)
                if OUTPUT_DIR:
                    if save_file:
                        save_file.close()
                    save_file_name = os.path.join(
                        OUTPUT_DIR, meat + os.path.extsep + 'mp3')
                    save_this_file = all((not os.path.exists(save_file_name),
                                          output_buffer.last_icy))
                    if save_this_file:
                        save_file = open(save_file, 'wb')
                        print("New file: {}".format(save_file.name), file=fout)
                    else:
                        save_file = None
                print(meat, end='', file=fout)
                elapsed = ''
                # Reset play timer
                start_time = time.time()
        else:
            # No new data, still mid-song
            # Erase the old time
            print(chr(8) * len(elapsed), end='', file=fout)
            # Print the new time
            elapsed = " ({})".format(elapsed_since(start_time))
            print(elapsed, end='', file=fout)
        # Get all the UI data out the door
        fout.flush()
        # Finally write the audio out to the client
        output_buffer.write(chunk)
        if save_file:
            save_file.write(chunk)
