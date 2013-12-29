Rio: (Radio without ads)
========================

A pseudo-DJ for internet radio.

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

First `python -m rio.rio [-o <path>]`. Then point your client at
`http://localhost:1986`. (reppin' funky '86!)

Songs will be saved at `<path>` if specified.
