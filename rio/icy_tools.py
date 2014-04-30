#!/usr/bin/env python
# coding: utf8

from __future__ import division, print_function

from collections import namedtuple
from math import ceil

from .utilities import unicode_dammit, pad

import logging
logger = logging.getLogger(__name__)


IcyData = namedtuple('IcyData', 'info data')


def read_icy_info(stream):
    """ Read and return the metadata out of an IceCast stream assuming
    that the metadata begins at byte 0.

    If there is no metadata return None.

    """
    # FIXME: when is it ok to return None?
    meatlen = stream.read(1)
    if meatlen:  # this is True for b'\x00'
        meatlen = ord(meatlen) * 16
        meat = stream.read(meatlen).strip()
        return unicode_dammit(meat).encode('utf8')


def parse_icy(stream, metaint):
    """ Yield tuples of (info, buf) indefinitely. """
    data = stream.read(metaint)
    icy = read_icy_info(stream)
    while data or icy:
        yield IcyData(icy.rstrip('\x00'), data)
        data = stream.read(metaint)
        icy = read_icy_info(stream)


def format_icy(icy_info):
    """ Return the icy_info as a 16-byte aligned bytestring, with an
    extra size byte at the front, as needed for ICY streams. """
    logger.debug("formatting icy_info {!r}".format(icy_info))
    icy = pad(icy_info, align=16, pad='\x00')
    return chr(int(ceil(len(icy) / 16.0))).encode('ascii') + icy


def without_icy_repeats(icy_data_stream):
    """ Return an iterable yielding the same icy_data_stream with
    consecutive repeated icy_info entries set to the empty string. """
    prev = b''
    for icy_data in icy_data_stream:
        if icy_data.info == prev:
            icy_data = IcyData(b'', icy_data.data)
        else:
            prev = icy_data.info
        yield icy_data


def validate_icy_stream(icy_data_stream):
    """ Return an iterable yielding the same icy_data_stream as long as
    icy_data.info contains no values between 1 and 31 and STREAM does not
    appear in icy_data.data. """
    for icy_data in icy_data_stream:
        info = icy_data.info
        bad_chars = set(chr(i) for i in range(1, 32))
        info_valid = all(c not in bad_chars for c in info)
        data_valid = "streamtitle" not in icy_data.data.lower()
        if not info_valid or not data_valid:
            logger.critical("icy_data.icy unprintable")
            raise StopIteration
        yield icy_data


def rebuffer_icy(icy_data_stream, metaint):
    """ Return an iterable yielding new ``IcyData`` tuples from an ICY
    stream where the buf lengths are changed to ``metaint``.


    We tag outgoing data with the tag from the *first* byte of that
    data.
    """
    buf = b''
    transmit_icy = None
    for icy, data in icy_data_stream:
        logger.debug('loop begin: icy({!r}), data({!r}), buf({!r})'
                     ' transmit_icy({!r})'.format(
                         icy, data, buf, transmit_icy))
        if not buf:
            # If the buffer is empty there is no leftover icy info
            transmit_icy = icy
        buf += data
        # Transmit blocks until buf is too short again
        transmitted = False
        while len(buf) >= metaint:
            transmit_buf, buf = buf[:metaint], buf[metaint:]
            icy_data = IcyData(transmit_icy, transmit_buf)
            logger.debug("transmit chunk {!r}".format(icy_data))
            yield icy_data
            if not transmitted:
                # Because we immediately transmit as much as possible,
                # there is guaranteed to be only one block left in
                # the buffer with 'old' icy info. Thus, the next block needs
                # the latest icy info.
                transmit_icy = icy
                transmitted = True

    if buf:
        # Flush out whatever is left
        padding = metaint - len(buf)
        data = buf + b'\x00' * padding
        icy_data = IcyData(icy, data)
        logger.debug("transmit chunk {!r}".format(icy_data))
        yield icy_data


def reconstruct_icy(icy_data_stream):
    """ Return an iterable of raw ICY stream data from an iterable
    of IcyData. """

    for info, data in icy_data_stream:
        icy = format_icy(info)
        yield data + icy
