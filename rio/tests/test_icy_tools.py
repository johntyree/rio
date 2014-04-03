#!/usr/bin/env python
# coding: utf8

from __future__ import division, print_function

import itertools as it
import string
import unittest
from cStringIO import StringIO
from math import ceil

from ..icy_tools import (
    IcyData, parse_icy, format_icy, read_icy_info, rebuffer_icy,
    without_icy_repeats, reconstruct_icy)
from ..utilities import by_chunks_of, pad


class Test_IcyTools(unittest.TestCase):

    def test_without_icy_repeats(self):
        self.in_stream = it.chain(
            (IcyData(b'foo', bytes(str(i))) for i in range(4)),
            (IcyData(b'barbar', bytes(str(i))) for i in range(4, 8)),
            (IcyData(b'baz', bytes(str(i))) for i in range(8, 10)),
            (IcyData(b'', bytes(str(i))) for i in range(10, 13)),
            (IcyData(b'quux', bytes(str(i))) for i in range(13, 16)),
        )
        self.out_stream = it.chain(
            (IcyData(b'foo', b'0'),),
            (IcyData(b'', bytes(str(i))) for i in range(1, 4)),
            (IcyData(b'barbar', b'4'),),
            (IcyData(b'', bytes(str(i))) for i in range(5, 8)),
            (IcyData(b'baz', b'8'),),
            (IcyData(b'', bytes(str(i))) for i in range(9, 10)),
            (IcyData(b'', bytes(str(i))) for i in range(10, 13)),
            (IcyData(b'quux', b'13'),),
            (IcyData(b'', bytes(str(i))) for i in range(14, 16)),
        )

        zipped = it.izip(without_icy_repeats(self.in_stream), self.out_stream)
        for result, expected in zipped:
            self.assertTupleEqual(result, expected)

    def test_empty_parse_icy(self):
        """ Extracting icy info from an empty string yields None. """
        data = StringIO(b'')
        expected = []
        result = list(parse_icy(data, 10))
        self.assertEqual(result, expected)

    def test_no_icy_extact_icy(self):
        icy_strings = (b'\x0000112233445566778899aabbccddeeff',
                       b'\x00Que Pasa?\x00\x00\x00\x00\x00\x00\x00')
        stream = StringIO(b''.join(icy_strings))
        result = tuple(parse_icy(stream, 32))
        expected = tuple(IcyData(b'', i[1:]) for i in icy_strings)
        self.assertSequenceEqual(result, expected)

    def test_no_data_extact_icy(self):
        """ Extract icy info from a stream with metaint 0. """
        icy_strings = (b'\x010123456789abcdef',
                       b'\x0200112233445566778899aabbccddeeff',
                       b'\x01Que Pasa?\x00\x00\x00\x00\x00\x00\x00')
        stream = StringIO(b''.join(icy_strings))
        result = tuple(parse_icy(stream, 0))
        expected = tuple(IcyData(i[1:], b'') for i in icy_strings)
        self.assertSequenceEqual(result, expected)

    def test_empty_read_icy_info(self):
        """ Reading icy info off of an empty string yields None. """
        in_stream = StringIO(b'')
        result = read_icy_info(in_stream)
        expected = None
        self.assertEqual(result, expected)

    def test_len0_reid_icy_info(self):
        """ Reading icy info of length zero yields an empty string. """
        in_stream = StringIO(b'\x00')
        result = read_icy_info(in_stream)
        expected = b''
        self.assertEqual(result, expected)

    def test_full_read_icy_info(self):
        """ Reading icy info from a stream returns the icy info string. """
        icy = pad(b"Woo wooooooo!!! Here we go, ya'll!")
        sample_data = chr(int(ceil(len(icy) / 16.0))).encode('ascii') + icy
        in_stream = StringIO(sample_data)
        result = read_icy_info(in_stream)
        expected = icy
        self.assertEqual(result, expected)

    def test_empty_format_icy(self):
        """ Formatting an empty string returns a single null character. """
        expected = b'\x00'
        result = format_icy(b'')
        self.assertEqual(result, expected)

    def test_full_format_icy(self):
        """ Formatting a normal string byte-aligns to 16. """
        msg = b'Woo woo!!!'
        expected = b'\x01' + pad(msg)
        result = format_icy(msg)
        self.assertEqual(result, expected)

    def test_larger_rebuffer_icy(self):
        """ Correctly rebuffer to a slightly larger chunk size. """
        old_metaint = 3
        new_metaint = 8

        data0, data1 = it.tee(it.cycle(string.printable))
        buf = it.imap(b''.join, by_chunks_of(old_metaint, data0))
        exp_buf = it.imap(b''.join, by_chunks_of(new_metaint, data1))

        icy_infos = 'foo barbar baz quux lork zerg guusje kriz'.split()
        exp_icy_infos = 'foo baz zerg'.split()

        icy_data_stream = (
            IcyData(i, b) for i, b in it.izip(icy_infos, buf))

        result = list(rebuffer_icy(new_metaint, icy_data_stream))
        expected = [
            IcyData(i, b) for i, b in it.izip(exp_icy_infos, exp_buf)]
        self.assertListEqual(result, expected)

    def test_smaller_rebuffer_icy(self):
        """ Correctly rebuffer to a slightly smaller chunk size. """
        old_metaint = 8
        new_metaint = 3

        data0, data1 = it.tee(it.cycle(string.printable))
        buf = it.imap(b''.join, by_chunks_of(old_metaint, data0))
        exp_buf = it.imap(b''.join, by_chunks_of(new_metaint, data1))

        icy_infos = 'foo barbar baz'.split()
        exp_icy_infos = 'foo foo foo barbar barbar barbar baz baz'.split()

        icy_data_stream = (
            IcyData(i, b) for i, b in it.izip(icy_infos, buf))

        result = list(rebuffer_icy(new_metaint, icy_data_stream))
        expected = [
            IcyData(i, b) for i, b in it.izip(exp_icy_infos, exp_buf)]
        self.assertListEqual(result, expected)

    def test_reconstruct_icy(self):
        in_stream = (
            IcyData(b'foo', b''.join(map(bytes, range(4)))),
            IcyData(b'barbar', b''.join(map(bytes, range(4, 8)))),
            IcyData(b'baz' * 6, b''.join(map(bytes, range(8, 10)))),
            IcyData(b'', b''.join(map(bytes, range(10, 13)))),
            IcyData(b'quux', b''.join(map(bytes, range(13, 16)))),
        )
        result = b''.join(reconstruct_icy(in_stream))
        expected = (
            b'\x01' + b'foo' + b'\x00' * 13 + b'0123'
            + b'\x01' + b'barbar' + b'\x00' * 10 + b'4567'
            + b'\x02' + b'baz' * 6 + b'\x00' * 14 + b'89'
            + b'\x00' + b'' + b'101112'
            + b'\x01' + b'quux' + b'\x00' * 12 + b'131415'
        )
        self.assertEqual(result, expected)
