#!/usr/bin/env python2
# coding: utf8

import sys

from .config import HOST, PORT
from .server import serve_on_port


def main():
    """Run main."""

    serve_on_port(host=HOST, port=PORT)

    return 0

if __name__ == '__main__':
    main()
