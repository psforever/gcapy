# GCAPy
A Python library and script to parse GCAP files. GCAP stands for Game CAPture and it is a file-format created by the PSForever project to store recorded game records from PlanetSide.
The library currently only reads, not writes, GCAP files.

GCAPy supports three actions: metadata display, record extraction, and game record statistics. Metadata display shows information about the GCAP file, record extraction carves out selected records, and game record statistics give information about PlanetSide packets.

If you are looking for some example captures to play with, download them from here: http://files.psforever.net/captures/

## Installation
This was tested on Mac OSX, Linux, and Windows under Cygwin. Here's the quick install:

      $ pip install git+https://github.com/psforever/gcapy.git

## Usage
Display the GCAP metadata

      $ gcapy -m file.gcap

Display multiple GCAP metadata

      $ gcapy -m file.gcap other-file.gcap

Extract records 1-20 and 45 and display as JSON

      $ gcapy -xjr 1-20,45 file.gcap

Extract records from 2255 onwards in binary

      $ gcapy -xor 2255- file.gcap

Run `gcapy -h` for the full usage statement.

GCAPy also comes with `gcapy-stats`, which parses GCAP files for statistics on packet types and their frequencies.
If you wanted to aggregate statistics for all GCAP files in the local directory, you would do this

      $ gcapy-stats *.gcap

The statistics are output to STDOUT and progress is show on STDERR. For multiple repeated stats collection,
a cache may be used

      $ gcapy-stats --cache gcap.cache *.gcap
      $ gcapy-stats --cache gcap.cache *.gcap # will load stats from cache and run much faster

## Notes
If you have downloaded GCAPy from GitHub without using pip, your .py files will have underscrores instead of hyphens. This will change the commands required to use the utility, i.e. gcapy-stats will be gcapy_stats.
