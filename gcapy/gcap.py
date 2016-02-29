# gcapy by Chord for PSForever
# gcap.py - implements GCAP parsing

import struct
import hashlib
import mmap
import os
import json

from collections import OrderedDict
from binascii import hexlify
from enum import IntEnum
from pprint import pprint

class GCAPFormatError(Exception):
    pass

class GCAPVersionError(Exception):
    pass

class RecordType(IntEnum):
    METADATA = 0
    GAME = 1

class GameRecordType(IntEnum):
    CRYPTO = 0
    PACKET = 1

class GameRecordPacketType(IntEnum):
    LOGIN = 0
    GAME = 1

class GameRecordDestination(IntEnum):
    SERVER = 0
    CLIENT = 1

class GCAP(object):
    HEADER_LEN = 4 + 1 + 1 + 8 + 16 + 8 + 8 + 8 + 32

    @staticmethod
    def _parse_header(header):
        headerFmt = [
                ("magic", "4s"),
                ("version_major", "B"),
                ("version_minor", "B"),
                ("capture_revision", "<Q"),
                ("guid", "16s"),
                ("start", "<Q"),
                ("end", "<Q"),
                ("record_count", "<Q"),
                ("sha256_hash", "32s")
        ]

        output = {}
        pointer = 0

        for k,v in headerFmt:
            unpackSz = struct.calcsize(v)
            result = struct.unpack_from(v, header, pointer)
            pointer += unpackSz

            output.update({k : result[0]})

        return output

    @staticmethod
    # Expects the file pointer to be pointing right after the header
    def _read_record_index(mmfile, max_records):
        start = GCAP.HEADER_LEN
        recordCnt = 0

        index = []
        while recordCnt < max_records:
            recordType = struct.unpack_from("B", mmfile, start)[0]
            recordSize = struct.unpack_from("I", mmfile, start+1)[0]
            item = [recordType, start+5, recordSize]

            index.append(item)

            start += 5 + recordSize
            recordCnt += 1

        return index

    @staticmethod
    def load(filename):

        fp = open(filename, 'rb')
        mmfile = mmap.mmap(fp.fileno(), 0, access = mmap.ACCESS_READ)
        fp.close()

        header = mmfile[0:GCAP.HEADER_LEN]

        if len(header) != GCAP.HEADER_LEN:
            raise GCAPFormatError("invalid header size. got %d, expected %d" % (len(header), GCAP.HEADER_LEN))

        parsed = GCAP._parse_header(header)

        if parsed['magic'] != "GCAP":
            raise GCAPFormatError("invalid magic bytes")

        headerHash = parsed['sha256_hash']
        compareHash = hashlib.sha256(header[0:GCAP.HEADER_LEN-32]).digest()

        if headerHash != compareHash: 
            raise GCAPFormatError("header corrupted")

        index = GCAP._read_record_index(mmfile, parsed['record_count'])

        return GCAP(".".join([str(parsed['version_major']), str(parsed['version_minor'])]),
                parsed, mmfile, index)

    def _decode_var_string(self, data):
        firstByte = struct.unpack_from("B", data)[0]

        # At the moment, all strings are treated the same
        # regardless of type
        stringType = firstByte & ~0xc0
        stringSize = (firstByte & 0xc0) >> 6

        size = 0
        nextPointer = 0
        stringOut = ""

        # 1 byte
        if stringSize == 0:
            size = struct.unpack_from("B", data, 1)[0]
            nextPointer = 1 + 1 + size
            stringOut = data[2:2+size]
        # 2 bytes
        elif stringSize == 1:
            size = struct.unpack_from("H", data, 1)[0]
            nextPointer = 1 + 2 + size
            stringOut = data[3:3+size]
        # 4 bytes
        elif stringSize == 2:
            size = struct.unpack_from("I", data, 1)[0]
            nextPointer = 1 + 4 + size
            stringOut = data[5:5+size]
        else:
            raise GCAPFormatError("unsupported variable string type")

        return (stringOut, nextPointer)

    def __init__(self, version, header, mmfile, index):
        version_parts = version.split(".")

        if len(version_parts) != 2:
            raise ValueError("version must be in the form of '1.0'")

        self.major = int(version_parts[0])
        self.minor = int(version_parts[1])
        self.header = header
        self.mmfile = mmfile
        self.index = index

        if self.major == 1 and self.minor == 0:
            pass
        else:
            raise GCAPVersionError("unsupported version " + version)

    def __iter__(self):
        for i in range(self.record_count()):
            yield self.get_record(i)

    def get_metadata(self):
        if self.record_count() > 0 and self.index[0][0] == RecordType.METADATA:
            # extract title and description
            inner_meta = self.get_record(0)

            # and add them to header metadata
            metadata = {
                    "version": ".".join([str(self.header['version_major']), str(self.header['version_minor'])]),
                    "capture_revision": self.header['capture_revision'],
                    "guid": self.header['guid'],
                    "start_time": self.header['start'],
                    "end_time": self.header['end'],
                    "record_count": self.header['record_count'],
                    "sha256_hash": self.header['sha256_hash'],
            }

            inner_meta['record'].update(metadata)

            return inner_meta
        else:
            raise GCAPFormatError("all GCAP files must have a metadata record as the first record")

    def record_count(self):
        return self.header['record_count']

    def get_record(self, which):
        if which < 0 or which > self.record_count():
            raise IndexError("invalid record index")

        # decode the record based off of type

        recType = self.index[which][0]
        recordStart = self.index[which][1]
        recordEnd = self.index[which][1] + self.index[which][2]
        rawRecord = self.mmfile[recordStart:recordEnd]

        result = { "type" : RecordType(recType).name, "number" : which }

        if recType == RecordType.METADATA:
            title, nextByte = self._decode_var_string(rawRecord)
            description, nextByte = self._decode_var_string(rawRecord[nextByte:])

            result.update({
                "record" : { "title" : title, "description" : description }
            })
        elif recType == RecordType.GAME:
            # type, timestamp, octal payload
            grecType = struct.unpack_from("B", rawRecord)[0]
            timestamp = struct.unpack_from("Q", rawRecord, 1)[0]
            rest = rawRecord[9:]
            innerRec = {}

            if grecType == GameRecordType.CRYPTO:
                raise GCAPFormatError("unsupported game record type")
            elif grecType == GameRecordType.PACKET:
                gamePacketType, gamePacketDest = struct.unpack_from("BB", rest)
                rec, nextByte = self._decode_var_string(rest[2:])

                innerRec = {
                        "type" : GameRecordPacketType(gamePacketType).name,
                        "destination" : GameRecordDestination(gamePacketDest).name,
                        "record" : rec
                }
            else:
                raise GCAPFormatError("unsupported game record type")

            result.update({
                "record" : {
                    "type": GameRecordType(grecType).name,
                    "timestamp": timestamp,
                    "record": innerRec
                }
            })

            return result
        else:
            raise GCAPFormatError("unsupported record type %d" % recType)

        return result

if __name__ == "__main__":
    gcap = GCAP.load("test.gcap")

    for i in gcap:
        print "Record: " + str(dict(i))
