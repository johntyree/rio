#!/usr/bin/env python2
# coding: utf8

from __future__ import print_function

import functools
import itertools as it
import json
import mimetools
import os
import sys
import time
from math import ceil

import logging
logger = logging.getLogger(__name__)


def consume(iterable):
    for _ in iterable:
        pass


def iflatten(iterables):
    """ Return the lazy equivalent of it.chain() """
    logger.info('begin iflatten')
    for i in iterables:
        logger.info('iflatten: next iterable')
        for e in i:
            yield e
    logger.info('end iflatten')


def sanitize_name(name):
    garbage = set(ur"~\/[];")
    return u''.join(c if c not in garbage else u'_' for c in name)


def trace(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        call = "\n{}({},{})".format(
            f.__name__,
            '\n\t'.join([''] + map(repr, args)),
            '\n\t'.join([''] + [
                '{!r}={!r}'.format(k, v) for k, v in kwargs.items()]))
        value = f(*args, **kwargs)
        ret = "{call}\n\t===\n\t{value}".format(**locals())
        print(ret, file=sys.stderr)
        return value
    return wrapper


def pad(s, pad=b'\x00', align=16):
    width = int(ceil(len(s) / float(align)) * align)
    return s.ljust(width, pad)


def by_chunks_of(sz, tail):
    head = tuple(it.islice(tail, sz))
    while head:
        yield head
        head = tuple(it.islice(tail, sz))


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
            print("Removing partial file: {!r}".format(self.fout.name))
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
    walkers = {mimetools.Message: lambda d: unicode(d)}
    pretty = unicode_dammit(d, walkers=walkers)
    js = json.dumps(pretty, indent=4).decode('utf8')
    return js


def deep_apply(f, data, walkers=None):
    custom = walkers or {}

    def safely_iterable(d):
        return type(d)(deep_apply(f, e, walkers) for e in d)

    def leaf(d):
        return f(d)

    def key_value_apply(d):
        return dict(deep_apply(f, kv, walkers) for kv in d.iteritems())

    walkers = {
        tuple: safely_iterable,
        list: safely_iterable,
        set: safely_iterable,
        unicode: leaf,
        bytes: leaf,
        dict: key_value_apply
    }
    walkers.update(custom)
    for typ in walkers.keys():
        if isinstance(data, typ):
            return walkers[typ](data)
    else:
        return data


def unicode_dammit(data, walkers={}):
    def convert(data):
        if not isinstance(data, unicode):
            try:
                data = unicode(data, encoding='utf8')
            except UnicodeDecodeError:
                try:
                    data = unicode(data, encoding='latin1')
                except UnicodeDecodeError:
                    pass
        return data
    return deep_apply(convert, data, walkers=walkers)


def render_headers(headers):
    pretty = {
        'icy-name': "Station",
        'icy-genre': "Genre",
        'icy-description': "Description",
        'icy-br': "Bitrate"}
    exclude = set((
        'connection',
        'icy-notice1',
        'icy-audio-info',
        'expires',
        'icy-pub',
        'icy-url',
        'cache-control',
        'icy-metaint',
        'icy-notice2',
        'range',
        'accept-ranges',
        'pragma'))
    txt = []
    for k, v in headers.items():
        if k.lower() not in exclude:
            key = pretty.get(k.lower(), k.title())
            txt.append("{}: {}".format(key, v))
    txt = '\n'.join(txt)
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
