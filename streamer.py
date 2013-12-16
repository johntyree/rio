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

streams = [
    'http://pub1.di.fm/di_space_dreams',
    'http://pub1.di.fm/di_lounge',
    'http://pub1.di.fm/di_chillout',
    'http://listen.radionomy.com/air-lounge',
    'http://listen.radionomy.com/aair-lounge-radio',
]

host = "john.bitsurge.net"
directory = os.path.expanduser('~/{host}/public/simply'.format(host=host))

bacteria = [
    'Musicplus - Jingle',
    'Joyeux Noel -',
    'Air Lounge Radio - Jingle',
    'Sfx - AdArrival',
    'AddictedToRadio',
]


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
    hostdir = os.path.join(homedir, host)
    url = os.path.relpath(url_file, start=hostdir)
    baseurl = 'http://{host}'.format(host=host)
    return urljoin(baseurl, url)


def rotten(meat):
    """ Make sure the meat isn't rotting with bact^H^H^H^Hcommercials. """
    return any(bacterium in meat or meat in bacterium
               for bacterium in bacteria)


metadata_regex = re.compile(
    r"StreamTitle='(?P<artist>.*)(?: - )(?P<title>.*?)';")
stream_title = "{artist} - {title}"


def parse_meat(stream):
    """ Read the metadata out of an IcyCast stream assuming that the
    metadata begins at byte 0.

    Return the metadata if it's ok.
    Return None if it looks like a comercial.

    """
    meatlen = stream.read(1)
    meatlen = ord(meatlen) * 16
    meat = stream.read(meatlen)
    if meat:
        sys.stderr.write("\n" + meat + "\n")
    if rotten(meat) or meatlen and not meat:
        return None
    match = metadata_regex.search(meat)
    if match:
        return stream_title.format(**match.groupdict())
    else:
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


def icystream(req, output_buffer):
    """Stream MP3 data, parsing the titles as you go and givng up when a
    commercial is detected.

    """
    interval = int(req.headers['icy-metaint'])
    stream = BufferedRequest(req)
    elapsed = ''
    start_time = time.time()
    fout = sys.stdout
    while True:
        chunk = stream.read(interval)
        meat = parse_meat(stream)
        if meat:
            if elapsed:
                fout.write("\n")
            fout.write(meat)
            elapsed = ''
            start_time = time.time()
        elif meat is None:
            fout.write(" - Rotten!\n")
            start_time = time.time()
            elapsed = ''
            return
        else:
            fout.write(chr(8) * len(elapsed))
            elapsed = " (" + elapsed_since(start_time) + ")"
            fout.write(elapsed)
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


def main():
    playlist = os.path.join(directory, 'simply.m3u')
    print("Playlist at:", playlist)
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(playlist, 'w') as pl:
        url_files = (url_file(url) for url in streams)
        url_file_urls = (url_file_url(url) + '\n' for url in url_files)
        pl.writelines(url_file_urls)

    for url in itertools.cycle(streams):
        filename = os.path.join(directory, url_file(url))
        with open(filename, 'wb') as f:
            print("Starting:", url, "->", f.name)
            r = requests.get(url, headers={'icy-metadata': 1}, stream=True)
            icystream(r, f)


if __name__ == '__main__':
    main()