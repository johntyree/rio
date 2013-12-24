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
    (options, args) = parser.parse_args()
    return (options, args)

opts, _ = parseargs()

HOST = opts.host
PORT = opts.port

ICY_METAINT = 8192
DIRECTORY = os.path.expanduser('~/{host}/public/simply'.format(host=HOST))

Ambient = (
    'http://pub1.di.fm/di_psybient',
    'http://pub1.di.fm/di_ambient',
    'http://pub1.di.fm/di_spacedreams',
)

Lounge = (
    'http://pub1.di.fm/di_lounge',
    'http://pub1.di.fm/di_chillout',
    'http://listen.radionomy.com/air-lounge',
    'http://listen.radionomy.com/aair-lounge-radio',
)

STREAMS = Lounge

Radionomy_ads = (
    'Musicplus - Jingle',
    'Radionomy - Radionomy',
    'Joyeux Noel -',
    'Un Noel plein de musique - Jingles',
    'Air Lounge Radio - Jingle',
    'Sfx - AdArrival',
    'AddictedToRadio',
)

DIfm_ads = (
    'ADWTAG',
    'www.di.fm/jobs',
    'Choose premium for the best audio experience',
    "There's more to Digitally Imported!",
)

AD_TITLES = Radionomy_ads + DIfm_ads
