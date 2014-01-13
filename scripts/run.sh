#!/bin/bash
set -e
git reset --hard
git pull
2to3 rio | patch -p0
python3 -m rio.rio --host john.bitsurge.net -o ~/john.bitsurge.net/private/streamed
