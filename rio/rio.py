#!/usr/bin/env python2
# coding: utf8

from .config import RioConfig
from .server import serve_on_port
from .utilities import render_dict


def list_genres(config):
    genres = config._config['genre']
    print(render_dict(genres))


def list_streams(config):
    for stream in config.all_streams:
        print(stream)


def main():
    """Run main."""

    config = RioConfig()

    if config.list_genres:
        list_genres(config)
    elif config.list_streams:
        list_streams(config)
    else:
        port = config.port
        host = config.host
        serve_on_port(host, port)

    return 0

if __name__ == '__main__':
    main()
