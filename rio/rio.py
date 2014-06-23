#!/usr/bin/env python2
# coding: utf8

from .config import RioConfig
from .server import serve_on_port
from .utilities import render_dict


def main():
    """Run main."""

    config = RioConfig()

    if config.list_genres:
        print(render_dict(config.genres))
    elif config.list_streams:
        for stream in config.streams:
            print(stream)

    else:
        port = config.port
        host = config.host
        serve_on_port(host, port)

    return 0

if __name__ == '__main__':
    main()
