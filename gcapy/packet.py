import sys
import struct
from enum import Enum

from . import packet_names

class PacketType(Enum):
    Control = 0
    Game = 1

class PacketDest(Enum):
    Server = 0
    Client = 1

class Packet:
    @staticmethod
    def getGamePacketNameById(id):
        assert id < len(packet_names.game_packet_names)

        return packet_names.game_packet_names[id][1]

    @staticmethod
    def getControlPacketNameById(id):
        assert id < len(packet_names.control_packet_names)

        return packet_names.control_packet_names[id][1]

    @staticmethod
    def get_name_by_id(ptype, id):
        if ptype == PacketType.Control:
            return Packet.getControlPacketNameById(id)
        elif ptype == PacketType.Game:
            return Packet.getGamePacketNameById(id)
        else:
            raise RuntimeError("Unsupported packet type: " + str(ptype))

    @staticmethod
    def is_unknown(ptype, id):
        if ptype == PacketType.Control:
            assert id < len(packet_names.control_packet_names)

            i = packet_names.control_packet_names[id]

            if len(i) >= 3:
                return i[2]
            else:
                return False
        elif ptype == PacketType.Game:
            assert id < len(packet_names.game_packet_names)

            i = packet_names.game_packet_names[id]

            if len(i) >= 3:
                return i[2]
            else:
                return False
        else:
            raise RuntimeError("Unsupported packet type: " + str(ptype))

    @staticmethod
    def get_type(data):
        if len(data) == 0:
            return (None, -1, False, 0)

        byte0 = ord(data[0]) if sys.version_info[0] < 3 else data[0]

        if byte0 == 0: # control packet
            if len(data) == 1:
                return (None, -1, False, 1)

            byte1 = ord(data[0]) if sys.version_info[1] < 3 else data[1]

            if byte1 >= len(packet_names.control_packet_names):
                return (None, byte0, False, 2)

            entry = packet_names.control_packet_names[byte1]

            return (PacketType.Control, entry[0], entry[2] if len(entry) ==3 else False, 2)
        else: # game packet
            if byte0 >= len(packet_names.game_packet_names):
                return (None, -1, False, 1)

            entry = packet_names.game_packet_names[byte0]

            return (PacketType.Game, entry[0], entry[2] if len(entry) == 3 else False, 1)

    @staticmethod
    def get_type_with_name(data):
        if len(data) == 0:
            return (None, -1, "", False, 0)

        byte0 = ord(data[0]) if sys.version_info[0] < 3 else data[0]

        if byte0 == 0: # control packet
            if len(data) == 1:
                return (None, -1, "", False, 1)

            byte1 = ord(data[1]) if sys.version_info[0] < 3 else data[1]

            if byte1 >= len(packet_names.control_packet_names):
                return (None, byte0, "", False, 2)

            entry = packet_names.control_packet_names[byte1]

            return (PacketType.Control, entry[0], entry[1], entry[2] if len(entry) ==3 else False, 2)
        else: # game packet
            if byte0 >= len(packet_names.game_packet_names):
                return (None, -1, "", False, 1)

            entry = packet_names.game_packet_names[byte0]

            return (PacketType.Game, entry[0], entry[1], entry[2] if len(entry) == 3 else False, 1)

    @staticmethod
    def unroll(data):
        ptype, pid, unknown, nextByte = Packet.get_type(data)
        headerEnd = nextByte

        if ptype != PacketType.Control:
            return [data]

        if pid == 0x03: # "MultiPacket"
            packets = []
            while nextByte < len(data):
                byteCnt = struct.unpack("B", data[nextByte])[0] if sys.version_info[0] < 3 else data[nextByte]
                nextByte += 1

                packets += Packet.unroll(data[nextByte:nextByte+byteCnt])
                nextByte += byteCnt

            return [data[:headerEnd]] + packets
        elif pid == 0x25: # "MultiPacketEx"
            sizes = [8, 16, 32]
            guards = [0xff, 0xffff]
            packets = []

            while nextByte < len(data):
                found = False
                for i,s in enumerate(sizes):
                    count = 0

                    if s == 8:
                        count = struct.unpack("B", data[nextByte])[0] if sys.version_info[0] < 3 else data[nextByte]
                        nextByte += 1
                    elif s == 16:
                        count = struct.unpack("H", data[nextByte:nextByte+2])[0]
                        nextByte += 2
                    elif s == 32:
                        count = struct.unpack("I", data[nextByte:nextByte+4])[0]
                        nextByte += 4

                    if i == len(guards) or count != guards[i]:
                        subpacket = data[nextByte:nextByte+count]
                        packets += Packet.unroll(subpacket)

                        nextByte += count
                        found = True
                        break

                if not found:
                    raise RuntimeError("Invalid MultiPacketEx")

            return [data[:headerEnd]] + packets

        elif pid == 0x09: # "SlottedMetaPacket0"
            return [data[:headerEnd+2]] +  Packet.unroll(data[headerEnd+2:])
        else:
            return [data]
