#!/usr/bin/env python2
# coding: utf8

from .config import RioConfig
from .server import serve_on_port


def main():
    """Run main."""
    config = RioConfig()
    port = config.port
    host = config.host

    serve_on_port(host, port)

    return 0

if __name__ == '__main__':
    main()
