import sys
import getopt
from functools import reduce

from .process import *
from . import util

# global exename for usage in the program
exename = ""

# placeholders for start and end of file
START_OF_FILE = -1
END_OF_FILE = 4000000000

def usage(reason = ''):
    if reason != '':
        print("Error: " + reason)
        print("")

    print("""\
usage: %s [options] file.gcap [file2.gcap..]

Action:
-m    Display GCAP metadata
-x    Extract GCAP records
-s    Run statistics on the selected Game Packets

Selection:
-r    select slices from the GCAP file starting at 1
      Examples:
        -r 1,2,3-10     selects records 1-10
        -r -            selects all records
        -r 5-           selects all records from 5 onwards
        -r 23           selects record 23

      Slicing will only work when one file is passed in. With multiple files,
      extraction and statistics will be run on all records.

Output modes:
-j    JSON output mode
-a    ASCII output mode (default)
-o    Binary output mode\
""" % exename)
    sys.exit(2)

def exit(code, reason=''):
    if reason != '':
        print(reason)

    sys.exit(code)

def parse_ranges(text):
    # remove all whitespace
    text = "".join(text.split())

    # look for multiple ranges in one argument
    ranges = text.split(',')
    output = []

    for r in ranges:
        if r == "":
            return []

        interval = r.split('-')

        # single number
        if len(interval) == 1:
            try:
                number = int(interval[0])

                if number < 1:
                    return []

                output.append((number, number))
            except ValueError as e:
                return []
        # range of numbers
        elif len(interval) == 2:
            try:
                # used to see if a maximum range endpoint was specified
                terminator = False

                lnumber = 0
                rnumber = 0

                if interval[0] == "":
                    lnumber = START_OF_FILE
                    terminator = True
                else:
                    lnumber = int(interval[0])

                    if lnumber < 1:
                        return []

                if interval[1] == "":
                    rnumber = END_OF_FILE
                    terminator = True
                else:
                    rnumber = int(interval[1])

                    if rnumber < 1:
                        return []

                # only compare if we have two numbers to compare
                if not terminator and lnumber > rnumber:
                    return []

                output.append((lnumber, rnumber))
            except ValueError as e:
                return []
        else:
            return []

    return output

"""
Returns a sorted set of unique, minimal ranges in O(nlogn) time
"""
def combine_ranges(ranges):
    # sort ranges in O(nlogn)
    sranges = sorted(ranges)
    minimal = []
    working = None

    for i,v in enumerate(sranges):
        if working is None:
            working = v

        # are we on the last element
        if i+1 == len(sranges):
            minimal.append(working)
            break

        next_range = sranges[i+1]

        # end time of current range is gt or eq to lower range of next
        # combine them
        if working[1] >= next_range[0]:
            if next_range[1] > working[1]:
                working = (working[0], next_range[1])
        else:
            minimal.append(working)
            working = None

    return minimal

def main():
    argv = sys.argv

    if len(argv) == 0:
        exit("First argument must be the current executable")
    else:
        global exename
        exename = argv[0]
        argv = argv[1:]

    try:
        opt, tail = getopt.getopt(argv, "hmxsr:jao", ["help"])
    except getopt.error as err:
        usage(err.msg)

    # option values
    opt_disp_meta = False
    opt_extract = False
    opt_stats = False

    opt_ranges = []

    opt_output_json = False
    opt_output_ascii = False
    opt_output_binary = False

    # final choices
    output = None
    actions = []

    # argument counter
    argument = 1

    for o,val in opt:
        if o == "--help" or o == "-h":
            usage()
        elif o == "-m":
            opt_disp_meta = True
        elif o == "-x":
            opt_extract = True
        elif o == "-s":
            opt_stats = True
        elif o == "-r":
            new_ranges = parse_ranges(val)

            if len(new_ranges) == 0:
                usage("Invalid range specification (argument %d)" % argument)

            opt_ranges.extend(new_ranges)
        elif o == "-j":
            opt_output_json = True
        elif o == "-a":
            opt_output_ascii = True
        elif o == "-o":
            opt_output_binary = True
        else:
            raise RuntimeError("Unhandled argument " + o)

        argument += 1

    ######################
    # files
    ######################

    if len(tail) == 0:
        usage("No files specified")

    ######################
    # actions
    ######################

    if opt_disp_meta:
        actions += [GCAPyAction.Metadata]
    if opt_extract:
        actions += [GCAPyAction.Extract]
    if opt_stats:
        actions += [GCAPyAction.Stats]

    # make sure at least one action has been specified
    if len(actions) == 0:
        usage("No action specified")

    soleAction = len(actions) == 1

    ######################
    # outputs
    ######################

    # make sure only one output has been specified
    amt = reduce(lambda x,y: x+y, [opt_output_json, opt_output_ascii, opt_output_binary])

    # if nothing was chosen, by default choose ascii
    if amt == 0:
        opt_output_ascii = True
    elif amt > 1:
        usage("Multiple output options provided")

    # we can only output binary when we are extracting
    if opt_output_binary:
        if not opt_extract and soleAction:
            usage("Cannot output binary for anything but record extraction")

        if os.isatty(sys.stdout.fileno()):
            error("refusing to output binary data to a terminal")
            exit(1)

    if opt_output_ascii:
        output = GCAPyOutput.Ascii
    elif opt_output_json:
        output = GCAPyOutput.Json
        util.interactive = False
    elif opt_output_binary:
        output = GCAPyOutput.Binary
        util.interactive = False

    ######################
    # process the ranges
    ######################

    #print("Ranges: " + str(opt_ranges))
    opt_ranges = combine_ranges(opt_ranges)
    #print("MinRanges: " + str(opt_ranges))

    # no ranges, assume the whole file
    if not len(opt_ranges):
        opt_ranges = [(START_OF_FILE, END_OF_FILE)]

    # TODO: make prints go to stderr
    # make sure ranges are only passed in when there is one file
    else:
        #if len(tail) > 1:
        #    warning("ranges are ignored when multiple files are processed")
        #    opt_ranges = [(START_OF_FILE, END_OF_FILE)]

        if opt_disp_meta and soleAction:
            warning("ranges specified but only displaying metadata")

    exit(process_gcapy(tail, opt_ranges, actions, output))

if __name__ == "__main__":
    main()
