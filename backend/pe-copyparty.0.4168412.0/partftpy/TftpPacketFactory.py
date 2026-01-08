# coding: utf-8
# vim: ts=4 sw=4 et ai:
from __future__ import print_function, unicode_literals

"a"


import logging

from .TftpPacketTypes import *
from .TftpShared import *

log = logging.getLogger("partftpy.TftpPacketFactory")


class TftpPacketFactory(object):
    "a"

    def __init__(self):
        self.classes = {
            1: TftpPacketRRQ,
            2: TftpPacketWRQ,
            3: TftpPacketDAT,
            4: TftpPacketACK,
            5: TftpPacketERR,
            6: TftpPacketOACK,
        }

    def parse(self, buffer):
        "a"
        log.debug("parsing a %d byte packet", len(buffer))
        (opcode,) = struct.unpack("!H", buffer[:2])
        log.debug("opcode is %d", opcode)
        packet = self.__create(opcode)
        packet.buffer = buffer
        return packet.decode()

    def __create(self, opcode):
        "a"
        if opcode not in self.classes:
            raise Exception("Unsupported opcode: %d" % opcode)

        packet = self.classes[opcode]()

        return packet
