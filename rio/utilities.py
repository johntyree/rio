#!/usr/bin/env python2
# coding: utf8

from __future__ import print_function

import os
import time


def persistently_apply(f, args=(), kwargs={}, tries=10):
    tries -= 1
    while tries:
        try:
            return f(*args, **kwargs)
        except:
            tries -= 1
    return f(*args, **kwargs)


class CompleteFileWriter(object):
    def __init__(self, fout):
        self.fout = fout

    def __getattr__(self, attr):
        return getattr(self.fout, attr)

    def __del__(self):
        if not self.fout.closed:
            self.fout.close()
            print("\nRemoving partial file: {!r}".format(self.fout.name))
            os.unlink(self.fout.name)


class Duplexer(object):
    ''' A collection which delegates attribute getting and setting to
    children.'''

    def __init__(self, children):
        self.__dict__['children'] = list(children)

    def __getattr__(self, attr):
        kids = list(getattr(child, attr) for child in self.children)
        return Duplexer(kids)

    def __call__(self, *args, **kwargs):
        rets = list(child(*args, **kwargs) for child in self.children)
        return Duplexer(rets)

    def __setattr__(self, attr, val):
        if attr in self.__dict__:
            self.__dict__[attr] = val
        else:
            for child in self.children:
                setattr(child, attr, val)

    def __iter__(self):
        return iter(self.children)

    def __repr__(self):
        return "{}: {!r}".format(self.__class__, self.children)

    def __str__(self):
        return "{}: {!s}".format(self.__class__, self.children)


def render_dict(d):
    return '\n'.join("{}: {}".format(key, val) for key, val in d.items())


def deep_apply(f, data):
    if isinstance(data, dict):
        newdata = {}
        for k, v in data.iteritems():
            newdata[deep_apply(f, k)] = deep_apply(f, v)
        return newdata
    elif isinstance(data, unicode) or isinstance(data, str):
        return f(data)
    elif hasattr(data, '__iter__'):
        typ = type(data)
        return typ(deep_apply(f, e) for e in data)
    else:
        return data


def unicode_damnit(data):
    def convert(data):
        try:
            data = unicode(data, encoding='utf8')
        except:
            try:
                data = unicode(data, encoding='latin1')
            except:
                pass
        return data
    return deep_apply(convert, data)


def render_headers(headers):
    msgs = (
        ('icy-name', "Station: {}"),
        ('icy-genre', "Genre: {}"),
        ('icy-br', "Bitrate: {}"),
    )
    txt = '\n'.join(msg.format(headers[hdr])
                    for hdr, msg in msgs if hdr in headers)
    return txt


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
