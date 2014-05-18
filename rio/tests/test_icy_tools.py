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
    without_icy_repeats, reconstruct_icy, validate_icy_stream, takewhile_tags)
from ..utilities import pad


class Test_IcyTools(unittest.TestCase):

    def test_without_icy_repeats(self):
        """ Don't repeat ICYINFO if it hasn't changed. """
        in_stream = it.chain(
            (IcyData(b'foo', bytes(str(i))) for i in range(4)),
            (IcyData(b'barbar', bytes(str(i))) for i in range(4, 8)),
            (IcyData(b'baz', bytes(str(i))) for i in range(8, 10)),
            (IcyData(b'', bytes(str(i))) for i in range(10, 13)),
            (IcyData(b'quux', bytes(str(i))) for i in range(13, 16)),
        )
        out_stream = it.chain(
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

        zipped = it.izip(without_icy_repeats(in_stream), out_stream)
        for result, expected in zipped:
            self.assertEqual(result, expected)

    def test_validate_icy_stream_good(self):
        """ A valid icy stream passes non-destructive validity check """
        icy_data_stream = [
            IcyData(u'école'.encode('utf-8'),
                    b''.join(map(bytes, range(4)))),
            IcyData(u'þíóáñ'.encode('utf-8'),
                    b''.join(map(bytes, range(4, 8)))),
            IcyData(u'éígïábñÓÍÍÑG¨'.encode('utf-8') * 6,
                    b''.join(map(bytes, range(8, 10)))),
            IcyData(b'\x33', b''.join(map(bytes, range(10, 13)))),
            IcyData(b'quux', b''.join(map(bytes, range(13, 16)))),
        ]
        validated = list(validate_icy_stream(icy_data_stream))
        self.assertListEqual(icy_data_stream, validated)

    def test_validate_icy_stream_bad(self):
        """ An invalid icy stream fails non-destructive validity check """
        icy_data_stream = [
            IcyData(u'école'.encode('utf-8'),
                    b''.join(map(bytes, range(4)))),
            IcyData(u'þíóáñ'.encode('utf-8'),
                    b''.join(map(bytes, range(4, 8)))),
            IcyData(u'éígïábñÓÍÍÑG¨'.encode('utf-8') * 6,
                    b''.join(map(bytes, range(8, 10)))),
            IcyData(b'\x03', b''.join(map(bytes, range(10, 13)))),
            IcyData(b'quux', b''.join(map(bytes, range(13, 16)))),
        ]
        validated = list(validate_icy_stream(icy_data_stream))
        self.assertListEqual(icy_data_stream[:3], validated)

    def test_takewhile_tags(self):
        icy_data_stream = [
            IcyData('a', '0'),
            IcyData('b', '1'),
            IcyData('c', '2', set(['AD'])),
            IcyData('d', '3')
        ]
        result = takewhile_tags(lambda s: not s == 'AD', icy_data_stream)
        self.assertListEqual(icy_data_stream[:2], list(result))

    def test_empty_parse_icy(self):
        """ Extracting icy_data from an empty string yields None. """
        data = StringIO(b'')
        expected = []
        result = list(parse_icy(data, 10))
        self.assertEqual(result, expected)

    def test_no_icy_extact_icy(self):
        """ Extract icy_data from a stream with no icy. """
        icy_strings = (
            b'00112233445566778899aabbccddeeff\x00',
            b'Que Pasa?\x00\x00\x00\x00\x00\x00\x00' + b'\x00' * 16 + b'\x00')
        stream = StringIO(b''.join(icy_strings))
        result = tuple(parse_icy(stream, 32))
        expected = tuple(IcyData(b'', i[:-1]) for i in icy_strings)
        self.assertSequenceEqual(result, expected)

    def test_no_data_extact_icy(self):
        """ Extract icy_data from a stream with metaint 0 (no data). """
        icy_strings = (b'\x010123456789abcdef',
                       b'\x0200112233445566778899aabbccddeeff',
                       b'\x01Que Pasa?')
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
        """ Rebuffer to a larger ICY_METAINT. """
        self._rebuffer_tester(8, 12)

    def test_smaller_rebuffer_icy(self):
        """ Rebuffer to a smaller ICY_METAINT. """
        self._rebuffer_tester(12, 8)
        return

    def test_reconstruct_icy(self):
        """ Reconstruct an icecast stream from icy_data. """
        in_stream = (
            IcyData(b'foo', b''.join(map(bytes, range(4)))),
            IcyData(b'barbar', b''.join(map(bytes, range(4, 8)))),
            IcyData(b'baz' * 6, b''.join(map(bytes, range(8, 10)))),
            IcyData(b'', b''.join(map(bytes, range(10, 13)))),
            IcyData(b'quux', b''.join(map(bytes, range(13, 16)))),
        )
        result = b''.join(reconstruct_icy(in_stream))
        expected = (
            b'0123' + b'\x01' + b'foo' + b'\x00' * 13
            + b'4567' + b'\x01' + b'barbar' + b'\x00' * 10
            + b'89' + b'\x02' + b'baz' * 6 + b'\x00' * 14
            + b'101112' + b'\x00' + b'' + b'\x00' * 0
            + b'131415' + b'\x01' + b'quux' + b'\x00' * 12
        )
        self.assertEqual(result, expected)

    def _rebuffer_tester(self, old_metaint, new_metaint):
        chunks = 8

        source = string.printable
        buflen = max(old_metaint, new_metaint) * chunks
        repeats = int(ceil(buflen / len(source)))
        data = source * repeats
        ratio = new_metaint / old_metaint

        icy_infos = 'foo barbar baz quux lork zerg nory guusje'.split()
        exp_icy_infos = [icy_infos[int(i * ratio)]
                         for i in range(int(ceil(chunks / ratio)))
                         if int(i * ratio) < len(icy_infos)]

        buf = (data[i:i + old_metaint]
               for i in range(0, len(data), old_metaint))
        exp_buf = (data[i:i + new_metaint]
                   for i in range(0, len(data), new_metaint))

        icy_data_stream = it.starmap(IcyData, it.izip(icy_infos, buf))

        result = list(rebuffer_icy(icy_data_stream, new_metaint))
        expected = list(it.starmap(IcyData, it.izip(exp_icy_infos, exp_buf)))

        # Pad the end of the data if it doesn't line up perfectly
        trim = len(result[-1].data) - len(result[-1].data.rstrip(b'\x00'))
        idx = slice(0, -trim if trim else None)
        trimmed = expected[-1].data[idx] + b'\x00' * trim
        expected[-1] = IcyData(expected[-1].info, trimmed)

        self.assertListEqual(result, expected)

if __name__ == '__main__':
    import nose  # noqa
    import cProfile
    cProfile.run('nose.main()', sort='cumtime')
