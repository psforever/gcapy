import sys
import os

interactive = True

def error(msg):
    _write_msg("error: " + msg)

def warning(msg):
    _write_msg("warning: " + msg)

def info(msg):
    _write_msg(msg)

def _write_msg(msg):
    if not interactive:
        sys.stderr.write(msg + "\n")
    else:
        print("I" + msg)

def file_exists(filename):
    return os.path.isfile(filename)
