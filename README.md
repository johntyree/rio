Rio: (Radio without ads)
========================

A pseudo-DJ for internet radio.

How does it work?
-----------------

Rio streams music from ShoutCast servers and examines the (ICY) metadata that
they send down. When it sees something it doesn't like, it switches to the next
stream in the list.


Dependencies
------------

 * requests

Installation
------------

The usual `python setup.py install` works fine, but I recommend `python
setup.py develop` so that you can continue to easily pull updates while the
project is in its infancy.


Configuration
-------------

Edit `config.py` to list the `STREAMS` and `AD_TITLES` that you know already.
As you hear an ad playing, note the title displayed and add it to `AD_TITLES`.
Over time, Rio will learn when to switch stations.


Running
-------

First `python -m rio.rio`. Then point your client at `http://localhost:1986`.
(reppin' funky '86!)

