#!/usr/bin/env python
# coding: utf8

from __future__ import division, print_function

from collections import namedtuple
from math import ceil

from .utilities import unicode_dammit, pad

import logging
logger = logging.getLogger(__name__)


IcyData = namedtuple('IcyData', 'info buf')


def read_icy_info(stream):
    """ Read and return the metadata out of an IcyCast stream assuming
    that the metadata begins at byte 0.

    If there is no metadata return None.

    """
    meatlen = stream.read(1)
    if meatlen:
        meatlen = ord(meatlen) * 16
        meat = stream.read(meatlen).strip()
        return unicode_dammit(meat).encode('utf8')


def parse_icy(stream, metaint):
    """ Yield tuples of (info, buf) indefinitely. """
    icy = read_icy_info(stream)
    data = stream.read(metaint)
    while icy is not None:
        yield IcyData(icy, data)
        icy = read_icy_info(stream)
        data = stream.read(metaint)


def format_icy(icy_info):
    """ Return the icy_info as a 16-byte aligned bytestring, with an
    extra size byte at the front, as needed for ICY streams. """
    icy = pad(icy_info, align=16, pad='\x00')
    return chr(int(ceil(len(icy) / 16.0))).encode('ascii') + icy


def without_icy_repeats(icy_data_stream):
    """ Return an iterable yielding the same icy_data_stream with
    consecutive repeated icy_info entries set to the empty string. """
    prev = b''
    for icy_data in icy_data_stream:
        if icy_data.info == prev:
            icy_data = IcyData(b'', icy_data.buf)
        else:
            prev = icy_data.info
        yield icy_data


def rebuffer_icy(metaint, icy_data_stream):
    """ Return an iterable yielding new ``IcyData`` tuples from an ICY
    stream where the buf lengths are changed to ``metaint``. """
    buf = b''
    transmit_icy = None
    for icy, data in icy_data_stream:
        if not buf:
            # If the buffer is empty there is no leftover icy info
            transmit_icy = icy
        buf += data
        # Transmit blocks until buf is too short again
        transmitted = False
        while len(buf) >= metaint:
            transmit_buf, buf = buf[:metaint], buf[metaint:]
            icy_data = IcyData(transmit_icy, transmit_buf)
            yield icy_data
            if not transmitted:
                # Because we immediately transmit as much as possible,
                # there is guaranteed to be only one block left in
                # the buffer with 'old' icy info. Thus, the next block needs
                # the latest icy info.
                transmit_icy = icy
            transmitted = True
        if transmitted:
            transmit_icy = icy

    if buf:
        # Flush out whatever is left
        padding = metaint - len(buf)
        yield IcyData(icy, buf + b'\x00' * padding)


def reconstruct_icy(icy_data_stream):
    """ Return an iterable of raw ICY stream data from an iterable
    of IcyData. """

    for msg, buf in icy_data_stream:
        icy = format_icy(msg)
        yield icy + buf
