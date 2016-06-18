import packet_names

from packet import Packet,PacketType, PacketDest

class Stats:
    def __init__(self, verbose=False):
        self.verbose = verbose

        self.records = 0
        self.control = 0
        self.game = 0
        self.invalid = 0
        self.unknown = 0
        self.game_types = [0]*len(packet_names.game_packet_names)
        self.control_types = [0]*len(packet_names.control_packet_names)

        # network stats
        self.to_client = 0
        self.to_server = 0
        self.size_accum = 0
        self.game_dst = [[0,0]]*len(packet_names.game_packet_names)
        self.control_dst = [[0,0]]*len(packet_names.control_packet_names)

    def __add__(self, other):
        self.records += other.records
        self.control += other.control
        self.game += other.game
        self.invalid += other.invalid
        self.unknown += other.unknown

        for i,v in enumerate(other.game_types):
            self.game_types[i] += v
        for i,v in enumerate(other.control_types):
            self.control_types[i] += v

        # network stats
        self.to_client += other.to_client
        self.to_server += other.to_server
        self.size_accum += other.size_accum

        for i,v in enumerate(other.game_dst):
            j = self.game_dst[i]
            self.game_dst[i] = [j[0] + v[0], j[1] + v[1]]
        for i,v in enumerate(other.control_dst):
            j = self.control_dst[i]
            self.control_dst[i] = [j[0] + v[0], j[1] + v[1]]

        return self

    def add(self, dst, data):
        ptype, pid, unknown, _ = Packet.get_type(data)

        self.records += 1

        if not ptype:
            self.invalid += 1
            return

        self.size_accum += len(data)

        if ptype == PacketType.Control:
            self.control += 1
            self.control_types[pid] += 1

            self.control_dst[pid][dst] += 1
        elif ptype == PacketType.Game:
            self.game += 1
            self.game_types[pid] += 1

            self.game_dst[pid][dst] += 1

        if dst == PacketDest.Server:
            self.to_server += 1
        elif dst == PacketDest.Client:
            self.to_client += 1

        if unknown:
            self.unknown += 1

    def stats(self):
        return {
            "records" : self.records,
            "control" : self.control,
            "game" : self.game,
            "invalid" : self.invalid,
            "unknown" : self.unknown,
            "game_types" : self.game_types,
            "control_types" : self.control_types
        }

    def pp(self):
        def fmtlist(a, showAmt=False):
            newArr = []

            for i,v in enumerate(a):
                amt = ""
                if showAmt:
                    amt = "%d " % v[1]
                newArr += ["%d. %s%s (0x%02x)" % (i+1, amt, v[2], v[0])]

            return "\n".join(newArr)


        unseenControlList = []
        unseenGameList = []

        controlFreq = []
        gameFreq = []

        for i,v in enumerate(self.control_types):
            controlFreq += [[i, v, Packet.get_name_by_id(PacketType.Control, i)]]
        for i,v in enumerate(self.game_types):
            gameFreq += [[i, v, Packet.get_name_by_id(PacketType.Game, i)]]

        controlFreq = sorted(controlFreq, key=lambda x: x[1], reverse=True)
        gameFreq = sorted(gameFreq, key=lambda x: x[1], reverse=True)

        for (i, v, n) in gameFreq:
            if v == 0 and not Packet.is_unknown(PacketType.Game, i):
                unseenGameList += [[i, v, n]]

        for (i, v, n) in controlFreq:
            if v == 0 and not Packet.is_unknown(PacketType.Control, i):
                unseenControlList += [[i, v, n]]

        #####################

        statistics = \
"""\
Records:     %d
 - Control:  %d
 - Game:     %d
Invalid:     %d
Unknown:     %d
""" % (self.records, self.control, self.game, self.invalid, self.unknown)

        #####################

        frequency =  \
"""\
Frequency (highest to lowest)

== Game ==
%s

== Control ==
%s
""" % (fmtlist(gameFreq, True), fmtlist(controlFreq, True))

        #####################

        unseen = \
"""\
Unseen packets

== Control (%d) ==
%s

== Game (%d) ==
%s
""" % (len(unseenControlList), fmtlist(unseenControlList),
        len(unseenGameList), fmtlist(unseenGameList))

        #####################

        print(statistics)
        print(frequency)
        print(unseen)

