import base64
from binascii import hexlify
from enum import Enum

from util import *
from gcap import *

class GCAPyAction(Enum):
    Metadata = 0
    Extract = 1
    Stats = 2

class GCAPyOutput(Enum):
    Ascii = 0
    Json = 1
    Binary = 2

def pp_task(action, output, files, ranges):
    action_name = ""
    output_name = ""

    if action is GCAPyAction.Metadata:
        action_name = "Displaying metadata for"
    elif action is GCAPyAction.Extract:
        action_name = "Extracting records from"
    elif action is GCAPyAction.Stats:
        action_name = "Gathering stats for GameRecords in"
    else:
        raise RuntimeError("unhandled action")

    if output is GCAPyOutput.Ascii:
        output_name = "text"
    elif output is GCAPyOutput.Json:
        output_name = "JSON"
    elif output is GCAPyOutput.Binary:
        output_name = "binary"
    else:
        raise RuntimeError("unhandled output")

    return "%s %s with the ranges %s and outputing in %s" % \
           (action_name, str(files), str(ranges), str(output_name))

def process_gcapy(files, ranges, actions, output):
    output_process = None # function reference for the output processor

    if output is GCAPyOutput.Ascii:
        output_process = output_ascii
    elif output is GCAPyOutput.Json:
        output_process = output_json
    elif output is GCAPyOutput.Binary:
        output_process = output_binary
    else:
        raise RuntimeError("unhandled output")

    # Step 1: fetch the required data
    # Step 2: output the data in the required format

    # fail fast
    for f in files:
        if not file_exists(f):
            error("missing specfied file " + f)
            return 1

    for f in files:
        gcap = None

        info("File: " + f)

        try:
            gcap = GCAP.load(f)
        except IOError:
            error("could not open %s for reading" % f)
            return 1
        except GCAPFormatError as e:
            error("GCAP format error: " + str(e))
            return 1
        except GCAPVersionError as e:
            error("GCAP version error: " + str(e))
            return 1

        for action in actions:
          if action is GCAPyAction.Metadata:
              output_process(gcap.get_metadata())
          elif action is GCAPyAction.Extract:
              for therange in ranges:
                  for r in get_gcap_range(gcap, therange):
                      output_process(r)
          elif action is GCAPyAction.Stats:
              pass

    return 0

def get_gcap_range(gcap, therange):
    max_record = gcap.record_count()

    for i in xrange(therange[0], therange[1]+1):
        if i < 1:
            continue

        if i >= max_record:
            break

        yield gcap.get_record(i)

# output processors
def output_ascii(data):
    template = ""
    rtype = data['type']
    number = data['number']
    record = data['record']

    if rtype == "METADATA":
        guid = hexlify(record['guid'])
        start = record['start_time']
        end = record['end_time']

        if end > start:
            delta = end - start
        else:
            delta = 0

        template = \
"""\
Title: "%s"
GUID: %s

Number of records: %d
Revision: %d
Start: %d    End: %d    Delta: %d seconds

Description:
"%s"
""" % (record['title'], guid, record['record_count'],
        record['capture_revision'], start, end, delta, record['description'])
    elif rtype == "GAME":
        gtype = record['type']
        time = float(record['timestamp'])/1e6 # microseconds since start of capture
        record = record['record']

        if gtype == "PACKET":
            ptype = record['type']
            dst = record['destination']
            contents = hexlify(record['record'])

            if dst == "CLIENT":
                src = "SERVER"
            else:
                src = "CLIENT"


            template = \
"""\
Game record %d at %.6fs is from %s to %s with contents %s\
""" % (number, time, src, dst, contents)

    print(template)

def output_json(data):
    rtype = data['type']
    record = data['record']

    if rtype == "METADATA":
        record['guid'] = hexlify(record['guid'])
        record['sha256_hash'] = hexlify(record['sha256_hash'])
    elif rtype == "GAME":
        gtype = record['type']
        record = record['record']

        if gtype == "PACKET":
            ptype = record['type']
            record['record'] = base64.encodestring(record['record']).strip()

    print(json.dumps(data))

def output_binary(data):
    rtype = data['type']
    record = data['record']

    if rtype == "GAME":
        gtype = record['type']
        record = record['record']

        if gtype == "PACKET":
            ptype = record['type']
            contents = record['record']
            sys.stdout.write(contents)
