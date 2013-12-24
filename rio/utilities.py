#!/usr/bin/env python2
# coding: utf8

from __future__ import print_function

import sys
import time


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


def print_headers(headers, file=sys.stdout):
    for key, val in headers.items():
        print("{key}: {val}".format(key=key, val=val), file=file)


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
