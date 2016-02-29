import sys
import os

def error(msg):
    sys.stderr.write("error: " + msg + "\n")

def warning(msg):
    sys.stderr.write("warning: " + msg + "\n")

def file_exists(filename):
    return os.path.isfile(filename)
