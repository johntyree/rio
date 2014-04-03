#!/usr/bin/env python2
# coding: utf8

from __future__ import print_function

import os
import re
import socket
import sys
import time
from math import ceil

from .utilities import (
    elapsed_since, render_headers, unicode_dammit,
    CompleteFileWriter, sanitize_name)
from .config import RioConfig



def build_headers(buf):
    """ Read the stream until the first blank line, building up a header
    dictionary.

    """
    hdrs = {}
    data = buf.read(4096)
    while True:
        line, _, data = data.partition(b'\r\n')
        if not line:
            buf.appendleft(data)
            break
        elif b':' in line:
            key, _, val = line.partition(b':')
            hdrs[key] = val
    return hdrs


# FIXME: This function is getting seriously crufty...
def icystream(stream, output_buffer, config=None):
    """Stream MP3 data, parsing the titles as you go and givng up when a
    commercial is detected.

    """

    config = config or RioConfig()

    print("\nStarting {!s}".format(stream))

    elapsed = ''
    fout = sys.stdout

    # Start the request, asking for metadata intervals and buffer
    # the input stream
    stream.data = BufferedRequest(stream.url, headers={'icy-metadata': 1})
    req = stream.data.req
    if not stream.data.ok:
        print("HTTP Error code {}".format(req.code), file=fout)
        return

    # If we got no headers back, assume that they are in-line. Everything
    # before the blank line is header, everything after is data
    if not req.headers:
        hdrs = build_headers(stream.data)
        req.headers = hdrs

    # Will we be receiving icy metadata? Forward it.
    interval = int(req.headers.get('icy-metaint', 0))
    if interval and config.forward_metadata:
        output_buffer = MetadataInjector(output_buffer, config.ICY_METAINT)
    else:
        output_buffer = MetadataInjector(output_buffer, 0)
    if not interval:
        print(u"No metadata recieved from stream."
              u" Ad detection will not work.", file=fout)

    start_time = time.time()

    msg = render_headers(req.headers)
    msg = '\t' + msg.replace('\n', '\n\t')
    print(msg)
    print(u"Networks: {!r}".format(stream.networks))
    bacteria = config.bacteria_for_stream(stream)
    print(u"Ad Sentinels: {!r}".format(
        [b.pattern.decode('utf8') for b in bacteria]))

    save_file = None

    OUTPUT_DIR = config.output_directory

    while True:
        try:
            updated = config.update()
        except ValueError as e:
            print(u"ValueError:", e)
        chunk = stream.read(interval)
        raw_meat = parse_meat(stream)
        if updated:
            bacteria = config.bacteria_for_stream(stream)
            print(u"\nAd Sentinels: {!r}".format(
                [b.pattern.decode('utf8') for b in bacteria]), file=fout)
            print(format_meat(output_buffer._current_icy), end='', file=fout)
            elapsed = ''

        # Save the config if it has been updated
        if config.config_age < config.age:
            config.write_config()
        if raw_meat:
            # We got some new metadata

            # If this song is complete but very short, it's
            # probably a commercial
            end_time = time.time()
            min_ad = config.min_ad_length
            max_ad = config.max_ad_length
            new_commercial = all((
                min_ad <= end_time - start_time <= max_ad,
                output_buffer._last_icy
            ))
            if new_commercial:
                if elapsed:
                    print('', file=fout)
                config.add_bacterium(stream.networks,
                                     format_meat(output_buffer._current_icy))

            bad_meat = rotten(raw_meat, bacteria)
            if bad_meat:
                # Found an ad title in the stream, abort!
                print(file=fout)
                show_rotten(raw_meat, bad_meat, file=fout)
                print(file=fout)

                elapsed = ''
                if save_file:
                    if time.time() - start_time < config.max_ad_length:
                        print("Song too short", file=fout)
                        del save_file
                        save_file = None
                    else:
                        save_file.close()
                return
            else:
                # Copy new icy metadata to clients
                output_buffer.icy = raw_meat
                # Put new metadata on a new line
                meat = format_meat(output_buffer.icy)
                if elapsed:
                    print(file=fout)
                if OUTPUT_DIR:
                    try:
                        os.makedirs(OUTPUT_DIR)
                    except OSError:
                        pass
                    if save_file:
                        if time.time() - start_time < config.max_ad_length:
                            print("Song too short", file=fout)
                            del save_file
                            save_file = None
                        else:
                            save_file.close()
                    safe_meat = sanitize_name(meat)
                    save_file_name = os.path.join(
                        OUTPUT_DIR, safe_meat + os.path.extsep + u'mp3')
                    save_this_file = all((
                        os.path.isdir(OUTPUT_DIR),
                        not os.path.exists(save_file_name),
                        output_buffer.last_icy,
                        not meat.startswith(u'Unknown format')))
                    if save_this_file:
                        try:
                            save_file = open(save_file_name.encode('utf8'),
                                             'wb')
                            save_file = CompleteFileWriter(save_file)
                            print("New file: {}".format(save_file.name),
                                  file=fout)
                        except IOError:
                            err = "Unable to save file: {}"
                            print(err.format(save_file_name))
                            save_file = None
                    else:
                        save_file = None
                print(meat, end='', file=fout)
                elapsed = ''
                # Reset play timer
                start_time = time.time()
        else:
            # No new data, still mid-song
            # Erase the old time
            print(chr(8) * len(elapsed), end='', file=fout)
            # Print the new time
            elapsed = " ({})".format(elapsed_since(start_time))
            print(elapsed, end='', file=fout)
        # Get all the UI data out the door
        fout.flush()
        # Finally write the audio out to the client
        output_buffer.write(chunk)
        if save_file:
            save_file.write(chunk)
