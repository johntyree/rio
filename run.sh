if [ -f 'CONVERTED' ]; then
	python3 -m rio.rio --host john.bitsurge.net
else
	2to3-3.1 rio | patch -p0 && touch 'CONVERTED' && git add 'CONVERTED'
	python3 -m rio.rio --host john.bitsurge.net
fi
