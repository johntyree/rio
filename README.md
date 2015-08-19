Rio: (Radio without ads)
========================

[![BuildStatus](https://api.travis-ci.org/johntyree/rio.svg)](http://travis-ci.org/johntyree/rio)

A pseudo-DJ for internet radio.

## Rewrite
This is an ambitious rewrite from scratch as an experiment on top of iterators.
The code is much nicer than the original implementation, but it is not
yet feature complete.

How does it work?
-----------------

Rio streams music from ShoutCast servers and examines the (ICY) metadata that
they send down. When it sees something it doesn't like, it switches to the next
stream in the list.


Installation
------------

The usual `python setup.py install` works fine, but I recommend `python
setup.py develop` so that you can continue to easily pull updates while the
project is in its infancy.


Configuration
-------------

Edit `config_data.json` to list the `stream`s and `ad`s that you know already.
As you hear an ad playing, note the title displayed and add it to `ad[network]`
. Rio will automatically flag a title if it looks too short to be a song. Over
time, Rio will learn when to switch stations.


Running
-------

    Usage: rio [options]

    Options:
    -h, --help            show this help message and exit
    -s, --shuffle         Play streams in random order
    -p PORT, --port=PORT  Port on which to listen for incoming connections
    -H HOST, --host=HOST  Host on which to listen for incoming connections
    -o DIR, --output=DIR  Directory in which to save incoming audio
    -g GENRE, --genre=GENRE
                            Musical genre (as defined in config file)
    -c CONFIG, --config=CONFIG
                            Config file containing streams, ads, and genres
    --list-streams        Show all streams and exit
    --list-genres         Show all genres and exit

**tldr;** First `rio -g lounge --shuffle [-o <DIR>]`. Then point your client at
`http://localhost:1986`. (reppin' funky '86!)

Songs will be saved to `<DIR>` if specified.

This version does not yet learn new ads as the old method was not robust
enough. Audio fingerprinting is being investigated as an alternative.
