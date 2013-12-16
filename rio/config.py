import os
import sys

HOST = "john.bitsurge.net"
PORT = int(sys.argv[1:] or 1986)

DIRECTORY = os.path.expanduser('~/{host}/public/simply'.format(host=HOST))

STREAMS = [
    'http://pub1.di.fm/di_space_dreams',
    'http://pub1.di.fm/di_lounge',
    'http://pub1.di.fm/di_chillout',
    'http://listen.radionomy.com/air-lounge',
    'http://listen.radionomy.com/aair-lounge-radio',
]

AD_TITLES = [
    'Musicplus - Jingle',
    'Joyeux Noel -',
    'Air Lounge Radio - Jingle',
    'Sfx - AdArrival',
    'AddictedToRadio',
]

