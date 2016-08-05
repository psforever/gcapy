import sys
import util
import sqlite3

from . import __version__
from gcap import *

def exit(code, reason=''):
    if reason is not '':
        print(reason)

    sys.exit(code)

def main():
    argv = sys.argv
    #conn = sqlite3.connect('gcap.db')
    conn = sqlite3.connect(':memory:')

    c = conn.cursor()

    c.execute('''CREATE TABLE captures(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guid BLOB
            )''')

    c.execute('''CREATE TABLE game_records(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            capture_id INTEGER,
            type INTEGER NOT NULL,
            destination INTEGER NOT NULL,
            idx INTEGER NOT NULL,
            subidx INTEGER NOT NULL,
            opcode1 TINYINT NOT NULL,
            opcode2 TINYINT NOT NULL,
            FOREIGN KEY(capture_id) REFERENCES captures(id)
            )''')

    # Load in GCAP files
    # Process files for all records
    # Load processed records in to SQLite for indexing
    # Present shell for interaction

    conn.commit()

if __name__ == "__main__":
    main()
