#!/usr/bin/env python
import sys
import argparse
import binascii
import shelve
from datetime import datetime
from pprint import PrettyPrinter

from .stats import Stats
from . import __version__
from . import packet_names
from .gcap import *
from .packet import Packet,PacketType, PacketDest

def error(msg):
    sys.stderr.write("error: " + msg + "\n")

def info(msg):
    sys.stderr.write(msg + "\n")

def main():
    parser = argparse.ArgumentParser(description='Gather stats on GCAP files')
    parser.add_argument('--cache', help='GCAP statistics cache')
    parser.add_argument('files', nargs='+', metavar='files', help='GCAP file')
    args = parser.parse_args()

    print("GCAPy Stats " + __version__)
    print("")

    processStart = datetime.now()

    stats = []
    okay = []
    failed = []
    cacheHits = 0

    gcap = None
    cache = None

    if args.cache:
        info("Using cache %s" % args.cache)
        cache = shelve.open(args.cache)

    for i,f in enumerate(args.files):
        sys.stderr.write("(%d/%d) " % (i+1, len(args.files)))

        try:
            gcap = GCAP.load(f)
            meta = gcap.get_metadata()
            key = binascii.hexlify(meta['record']['guid']) if sys.version_info[0] < 3 else meta['record']['guid'].hex()

            if cache is not None:
                if cache.has_key(key):
                    info("Loaded '%s' from the cache" % f)
                    cacheHits += 1

                    stats += [cache[key]]
                    okay += [[f, meta]]
                    gcap.close()
                    continue

            fStats = process(f, gcap, Stats())

            if cache is not None:
                cache[key] = fStats
                cache.sync()

            stats += [fStats]
            okay += [[f, meta]]
        except IOError:
            msg = "could not open %s for reading" % f
            error(msg)
            failed += [[f, msg]]
        except GCAPFormatError as e:
            msg = "GCAP format error: " + str(e)
            error(msg)
            failed += [[f, msg]]
        except GCAPVersionError as e:
            msg = "GCAP version error: " + str(e)
            error(msg)
            failed += [[f, msg]]
        finally:
            if gcap:
                gcap.close()

    if cache is not None:
        cache.close()

    processEnd = datetime.now()

    print("Started: " + str(processStart))
    print("Ended:   " + str(processEnd))
    print("Time:    " + str(processEnd-processStart))
    print("")

    note = ""

    if cache is not None:
        if cacheHits < len(okay):
            note = " (%d from cache)" % cacheHits
        else:
            note = " (all cached)"

    print("Statistics generated from %d files%s" % (len(okay), note))

    for o in okay:
        print(" - %s (records %d, GUID %s)" % (o[0],
            o[1]['record']['record_count'],
            binascii.hexlify(o[1]['record']['guid']) if sys.version_info[0] < 3 else o[1]['record']['guid'].hex()
            )
        )

    if len(failed):
        print("")
        print("There were %d failed files" % len(failed))
        for f in failed:
            print(" - %s (%s)" % (f[0], f[1]))

    # everything failed
    if len(okay) == 0:
        return

    print("")

    all_stats = Stats()

    total = 0

    # combine stats
    for s in stats:
        total += s.records
        all_stats += s

    all_stats.pp()

def process(f, gcap, stats):
    recordNum = gcap.record_count()

    maxProgressLen = len("100%")
    goBack = "\b"*maxProgressLen
    goForward = " "*maxProgressLen

    sys.stderr.write("Processing '%s' %s" % (f, goForward))
    for i,orec in enumerate(gcap):
        progress = "%d%%" % (int(float(i+1)/ float(recordNum) * 100))

        sys.stderr.write(goBack + progress + goForward[len(progress):])

        rtype = orec['type']
        record = orec['record']

        if rtype == "GAME":
            gtype = record['type']
            record = record['record']

            if gtype == "PACKET":
                ptype = record['type']
                dst = record['destination']
                raw = record['record']

                # perform packet unrolling
                if dst == "SERVER":
                    unrolledPackets = Packet.unroll(raw)

                    for p in unrolledPackets:
                        stats.add(PacketDest.Server, p)
                else:
                    stats.add(PacketDest.Client, raw)

    sys.stderr.write("\n")

    # free mmfile
    gcap.close()

    return stats

if __name__ == "__main__":
    main()
