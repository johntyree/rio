#!/usr/bin/env python2
# coding: utf8

from __future__ import print_function

import json
import itertools
import optparse
import os
import random
import re
import sys

from .utilities import unicode_damnit, persistently_apply

default_config = os.path.join(os.path.dirname(__file__), 'config_data.json')


def load_config(fname):
    data = []
    skips = (b'//',)
    with open(fname, 'rb') as f:
        data = [l.decode('utf8')
                for l in f
                if not any(l.strip().startswith(s) for s in skips)]
    try:
        data = persistently_apply(json.loads, args=(u''.join(data),))
    except ValueError as e:
        print("Could not load config: {}".format(e), file=sys.stderr)
        data = {}
    return unicode_damnit(data)


def parseargs(argv=sys.argv):
    parser = optparse.OptionParser()
    parser.add_option('-s', '--shuffle', action='store_true', dest='shuffle',
                      help="Play streams in random order")
    parser.add_option('-p', '--port', type=int, default=1986,
                      help="Port on which to listen for incoming connections")
    parser.add_option('-H', '--host', default="localhost",
                      help="Host on which to listen for incoming connections")
    parser.add_option('-o', '--output', default=None,
                      help="Directory in which to save incoming audio")
    parser.add_option('-g', '--genre', default='lounge',
                      help="Musical genre (as defined in config file)")
    parser.add_option('-c', '--config', default=default_config,
                      help="Config file containing streams, ads, and genres")
    parser.add_option('--list-streams', action='store_true',
                      dest='list_streams', help="Show all streams and exit")
    parser.add_option('--list-genres', action='store_true',
                      dest='list_genres', help="Show all genres and exit")
    (options, args) = parser.parse_args(argv)
    return (options, args)


class Stream(object):

    def __init__(self, name, url, networks):
        self.name = name
        self.url = url
        self.networks = networks
        self.data = None

    def read(self, bytes):
        if self.data is None:
            raise RuntimeError("Stream data not set")
        return self.data.read(bytes)

    def __str__(self):
        msg = "<Stream {name!s}: {url!r}>"
        return msg.format(**vars(self))

    def __repr__(self):
        msg = "Stream(name={name}, url={url}, \
               networks={networks}, data={data})"
        return msg.format(**vars(self))


def make_stream(name, rioconfig):
    streamdata = rioconfig._config['stream'][name]
    url = streamdata['url']
    network = streamdata['network']
    stream = Stream(name, url, network)
    return stream


class RioConfig(object):

    _opts = None
    _args = None
    _config = None
    ICY_METAINT = 8192
    # The number of seconds required before something isn't an ad
    min_ad_length, max_ad_length = 3, 120
    forward_metadata = False

    def __init__(self, argv=sys.argv, config_file=None):
        if not self._opts:
            self._opts, self._args = parseargs(argv)
            self.port = self._opts.port
            self.host = self._opts.host
        self.config_file = config_file or self._opts.config
        od = self._opts.output
        # FIXME: can this postprocessing be done in optparse?
        self.output_directory = os.path.expanduser(od) if od else None
        self.age = 0.0
        self.update()

    def render_config(self):
        raw = json.dumps(self._config, indent=4)
        return '\n'.join(l.rstrip() for l in raw.splitlines())

    def write_config(self, fname=None):
        if fname is None:
            fname = self.config_file
        with open(fname, 'w') as fout:
            fout.write(self.render_config())
        # Force an update
        self.age = 0

    @property
    def list_streams(self):
        return self._opts.list_streams

    @property
    def list_genres(self):
        return self._opts.list_genres

    @property
    def config_age(self):
        return os.stat(self.config_file).st_mtime

    def add_bacterium(self, networks, bacterium):
        msg = "New bacterium for networks {}: {!r}"
        print(msg.format(networks, bacterium))
        for net in networks:
            self._config['ad'].setdefault(net, []).append(bacterium)
        self.write_config()

    @property
    def bacteria(self):
        self.update(safe=True)
        if self._bacteria is None:
            self._bacteria = {
                net: [re.compile(ad.encode('utf8')) for ad in ads]
                for net, ads in self._config['ad'].items()}
        return self._bacteria

    def bacteria_for_stream(self, stream):
        bacteria = {bacterium
                    for net in stream.networks
                    for bacterium in self.bacteria.get(net, [])}
        return bacteria

    @property
    def all_streams(self):
        self.update(safe=True)
        streams = [make_stream(name, self)
                   for genre, names in self._config['genre'].items()
                   for name in names]
        return streams

    @property
    def streams(self):
        self.update(safe=True)
        if self._streams is None:
            self._streams = [make_stream(name, self) for name in
                             self._config['genre'][self._opts.genre]]
        return self._streams

    def cycle_streams(self):
        lasturl = ''
        streams = list(self.streams)
        while True:
            age = self.age
            # Rotate the list to the last one
            try:
                previous = [s.url for s in self.streams].index(lasturl)
                nextidx = (previous + 1) % len(streams)
            except ValueError:
                nextidx = 0
            streams = streams[nextidx:] + streams[:nextidx]
            if self._opts.shuffle:
                random.shuffle(streams)
            for stream in itertools.cycle(streams):
                lasturl = stream.url
                yield stream
                if self.age != age:
                    break

    def update(self, safe=False):
        if self.config_age <= self.age:
            return False
        new_config = load_config(self.config_file)
        if new_config:
            self._config = new_config
            self.age = self.config_age
            self._bacteria = None
            self._streams = None
            return self.age
        else:
            msg = "Invalid JSON in config?"
            if safe:
                print("ValueError: {}".format(msg), file=sys.stderr)
            else:
                raise ValueError(msg)
        return False

if __name__ == '__main__':
    # A validator
    RioConfig()
