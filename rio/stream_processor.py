#!/usr/bin/env python
# coding: utf8

from __future__ import division, print_function

import re

from .icy_tools import reconstruct_icy
from .utilities import unicode_dammit

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def icy_info_buf_size(icy_data_stream):
    """ Return an iterable that yields tuples of (icy_info, buf_size). """

    current_bufsize, current_icy = 0, b''
    for icy_data in icy_data_stream:
        if icy_data.info != current_icy:
            # We have new icy_info, the old one has finished
            logger.info("ICYINFO({!r}) size {}".format(
                current_icy, current_bufsize))
            # Report the icy_info and size
            yield current_icy, current_bufsize

            # Reinitialize
            current_icy = icy_data.info
            current_bufsize = 0
            logger.info("ICYINFO({!r}) BEGIN".format(icy_data.info))

        # Add this chunk of data to our tally
        current_bufsize += len(icy_data.data)


def write_stream_to_buf(icy_data_stream, buf, with_icy=True):
    """ Write the stream to a buffer, optionally with ICYINFO in it. """

    if with_icy:
        for chunk in reconstruct_icy(icy_data_stream):
            yield buf.write(chunk)
            logger.debug("chunk written")
    else:
        for icy_data in icy_data_stream:
            yield buf.write(icy_data.data)
            logger.debug("chunk written")
    logger.debug("finished writing stream")


def regex_matches(icy_data_stream, regexen):
    """ Return an iterable of IcyData where 'AD' has been added to the
    `tags` if any of `regexen` match `.info`. """

    def rotten(meat, bacteria):
        """ Make sure the meat isn't rotting with bact^H^H^H^Hcommercials. """
        infections = [bacterium.pattern
                      for bacterium in bacteria if bacterium.search(meat)]
        return infections

    for icy_data in icy_data_stream:
        matches = [r.pattern for r in regexen if r.search(icy_data.info)]
        for m in matches:
            msg = '''Rotten! {!r} <-> {!r}'''.format(icy_data.info, m)
            logger.info(msg)
            icy_data.tags.add('AD')
        yield icy_data


def prettify_icy_info(icy_data_stream):
    """ Return an iterable of IcyData where the icy_info has been
    normalized to utf-8 encoded '{artist} - {title}. """

    artist_title_regex = re.compile(
        ur"StreamTitle='(?:(?P<artist>.*)\s+-\s+)?(?P<title>.+?)';")
    stream_title = u"{artist} - {title}"

    for icy_data in icy_data_stream:
        meat = icy_data.info
        if meat:
            meat = unicode_dammit(icy_data.info)
            match = artist_title_regex.search(meat)
            if match:
                data = match.groupdict()
                if data['artist']:
                    meat = stream_title.format(**data)
                else:
                    meat = u'{title}'.format(**data)
            else:
                meat = u"Unknown format: {!r}".format(meat)
            meat = meat.replace(u'\x00', u'').strip()
        icy_data.info = meat
        yield icy_data
