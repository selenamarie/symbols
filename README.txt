=======
Symbols
=======

Symbols is a library for loading and querying Breakpad-compatible symbol data.

Raw symbols data is available at http://symbols.mozilla.org


==========
Installing
==========

This is real rough. :)

Start by creating a virtualenv & pip install -r requirements.txt

Make sure you have a local copy of PostgreSQL running.

Copy config.py.dist to config.py and edit sa_url to fix connection params.

Then, run: ./model.py to create a PostgreSQL database

Then, edit __main__ in symbols.py to point it at a directory of some files containing paths to symbol files. :)

TODO
* Make this configman'd
* Add remove() capability
