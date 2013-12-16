#!/usr/bin/env python3
# coding: utf-8
# GistID: 7799767

from __future__ import print_function

# import cStringIO
import itertools
import os
import re
import requests
import sys
import time
from urllib2 import urlparse
urlparse, urljoin = urlparse.urlparse, urlparse.urljoin

from .config import STREAMS
from .config import AD_TITLES as bacteria


metadata_regex = re.compile(
    r"StreamTitle='(?P<artist>.*)(?: - )(?P<title>.*?)';")
stream_title = "{artist} - {title}"


def url_file(url):
    """ Return a reasonable filename for the given url. """
    sep = os.path.sep
    u = urlparse(url)
    host = u.netloc.replace('.', '_')
    path = '_-_'.join(u.path.strip(sep).split(sep))
    filename = '_-_'.join((host, path))
    return os.path.join(directory, filename)


def url_file_url(url_file):
    homedir = os.path.expanduser('~')
    hostdir = os.path.join(homedir, HOST)
    url = os.path.relpath(url_file, start=hostdir)
    baseurl = 'http://{host}'.format(host=HOST)
    return urljoin(baseurl, url)


def rotten(meat):
    """ Make sure the meat isn't rotting with bact^H^H^H^Hcommercials. """
    if meat:
        for bacterium in bacteria:
            if bacterium in meat or meat in bacterium:
                print("{} <-> {}!".format(meat, bacterium))
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

    if meatlen:

        meatlen = ord(meatlen) * 16
        meat = stream.read(meatlen).strip()

        if meat:
            print("\n{}".format(meat), file=sys.stderr)

        if rotten(meat):
            return None

        match = metadata_regex.search(meat)
        if match:
            return stream_title.format(**match.groupdict())

    return ''


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


def icystream(url, output_buffer):
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
    try:
        interval = int(req.headers['icy-metaint'])
    except KeyError as e:
        print(e)
        interval = 0
    stream = BufferedRequest(req)

    start_time = time.time()
    while True:
        chunk = stream.read(interval)
        meat = parse_meat(stream)
        if meat:
            if elapsed:
                print(file=fout)
            fout.write(meat)
            elapsed = ''
            start_time = time.time()
        elif meat is None:
            # Found an ad title in the stream, abort!
            print(" - Rotten!", file=fout)
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


def streams_to_playlist(filename, streams):
    playlist = os.path.join(directory, 'simply.m3u')
    print("Playlist at:", playlist)
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(playlist, 'w') as pl:
        url_files = (url_file(url) for url in STREAMS)
        url_file_urls = (url_file_url(url) + '\n' for url in url_files)
        pl.writelines(url_file_urls)



if __name__ == '__main__':
    main()
