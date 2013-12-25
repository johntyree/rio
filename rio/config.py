#!/usr/bin/env python2
# coding: utf8

import optparse
import os


def parseargs():
    parser = optparse.OptionParser()
    parser.add_option('-p', '--port', type=int, default=1986,
                      help="Port on which to listen for clients")
    parser.add_option('-H', '--host', default="localhost",
                      help="Our hostname")
    parser.add_option('-o', '--output', default=None,
                      help="Directory for saving incoming audio to")
    (options, args) = parser.parse_args()
    return (options, args)

opts, _ = parseargs()

HOST = opts.host
PORT = opts.port
OUTPUT_DIR = os.path.expanduser(opts.output) if opts.output else None


ICY_METAINT = 8192
DIRECTORY = os.path.expanduser('~/{host}/public/simply'.format(host=HOST))

Ambient = (
    'http://pub1.di.fm/di_psybient',
    'http://pub1.di.fm/di_ambient',
    'http://pub1.di.fm/di_spacedreams',
    'http://pub1.di.fm/di_chillout',
)

Lounge = (
    'http://dallas68.somafm.com',
    'http://listen.radionomy.com/aair-lounge-radio',
    'http://listen.radionomy.com/air-lounge',
    'http://206.217.201.137:8059'
    'http://pub1.di.fm/di_lounge',
    'http://pub1.di.fm/di_chillout',
)

Pound = (
    'http://pub1.di.fm/di_harddance',
    'http://pub1.di.fm/di_hardstyle',
    'http://pub1.di.fm/di_handsup',
    'http://pub1.di.fm/di_hardcore',
)

Dance = (
    'http://pub1.di.fm/di_discohouse',
    'http://pub1.di.fm/di_funkyhouse',
    'http://wms-13.streamsrus.com:13930',
    'http://listen.radionomy.com/aqua-radio-online',
    'http://listen.radionomy.com/peripou-web-radio',
)

STREAMS = Lounge

SomaFM_ads = (
    'Please Donate to support',
)

Radionomy_ads = (
    'Radionomy - Radionomy',
    u"Tte l'équipe vous souhaite un - Jingles",
    r"Air Lounge Radio - Jingle ?\d*",
    r'Musicplus - Jingle intro ?\d*$',
    'Sfx - AdArrival',
    'AddictedToRadio',
)

DIfm_ads = (
    'ADWTAG',
    r'www\.di\.fm/jobs',
    'Choose premium for the best audio experience',
    "There's more to Digitally Imported!",
)

AD_TITLES = set(Radionomy_ads + DIfm_ads + SomaFM_ads)
