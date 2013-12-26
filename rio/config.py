#!/usr/bin/env python2
# coding: utf8

import ast
import itertools
import optparse
import os
import re
import sys

from utilities import unicode_damnit

default_config = os.path.join(os.path.dirname(__file__), 'config_data.py')


def load_config(fname):
    data = []
    with open(fname) as f:
        for line in f:
            if not any(line.strip().startswith(s) for s in ('from', '#')):
                data.append(line.decode('utf8'))
    data = ast.literal_eval(u''.join(data))
    return unicode_damnit(data)


def parseargs(argv=sys.argv):
    parser = optparse.OptionParser()
    parser.add_option('-p', '--port', type=int, default=1986,
                      help="Port on which to listen for clients")
    parser.add_option('-H', '--host', default="localhost",
                      help="Our hostname")
    parser.add_option('-o', '--output', default=None,
                      help="Directory for saving incoming audio to")
    parser.add_option('-g', '--genre', default='lounge',
                      help="Genre to stream as defined in the config file")
    parser.add_option('-c', '--config', default=default_config,
                      help="Config file containing streams, ads, and genres")
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
        self.age = None
        self.update()

    @property
    def bacteria(self):
        self.update()
        if self._bacteria is None:
            self._bacteria = {net: [re.compile(ad) for ad in ads]
                              for net, ads in self._config['ad'].items()}
        return self._bacteria

    def bacteria_for_stream(self, stream):
        bacteria = {bacterium
                    for net in stream.networks
                    for bacterium in self.bacteria[net]}
        return bacteria

    @property
    def streams(self):
        self.update()
        if self._streams is None:
            self._streams = [make_stream(name, self) for name in
                             self._config['genre'][self._opts.genre]]
        return self._streams

    def cycle_streams(self):
        lasturl = ''
        while True:
            age = self.age
            # Rotate the list to the last one
            try:
                previous = [s.url for s in self.streams].index(lasturl)
            except ValueError:
                previous = 0
            streams = self.streams[previous:] + self.streams[:previous]
            for stream in itertools.cycle(streams):
                lasturl = stream.url
                yield stream
                if self.age != age:
                    break

    def update(self):
        config_age = os.stat(self.config_file).st_mtime
        if config_age == self.age:
            return False
        self._config = load_config(self.config_file)
        self.age = config_age
        self._bacteria = None
        self._streams = None
        return self.age
