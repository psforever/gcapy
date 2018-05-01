GCAPy
=====

A Python library and script to parse GCAP files. GCAP stands for Game
CAPture and it is a file-format created by the PSForever project to
store recorded game records from PlanetSide. The library currently only
reads, not writes, GCAP files.

GCAPy supports three actions: metadata display, record extraction, and
game record statistics. Metadata display shows information about the
GCAP file, record extraction carves out selected records, and game
record statistics give information about PlanetSide packets.

Installation
------------

This was tested with Python 2.7 on Mac OSX and should work on all OS's. Here's
the quick install:

::

      $ git clone https://github.com/psforever/gcapy
      $ cd gcapy/
      $ pip install .

Usage
-----

Display the GCAP metadata $ gcapy -m file.gcap

Display multiple GCAP metadata $ gcapy -m file.gcap other-file.gcap

Extract records 1-20 and 45 and display as JSON $ gcapy -xjr 1-20,45
file.gcap

Extract records from 2255 onwards in binary $ gcapy -xor 2255- file.gcap

Run ``gcapy -h`` for the full usage statement.
