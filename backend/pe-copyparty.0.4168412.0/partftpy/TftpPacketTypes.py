# coding: utf-8
# vim: ts=4 sw=4 et ai:
from __future__ import print_function, unicode_literals

"a"


import logging
import struct
import sys

from .TftpShared import *

log = logging.getLogger("partftpy.TftpPacketTypes")


class TftpSession(object):
    "a"

    pass


class TftpPacketWithOptions(object):
    "a"

    def __init__(self):
        self.options = {}

    def decode_options(self, buffer):
        "a"

        log.debug("decode_options: buffer is %d bytes: %r", len(buffer), buffer)

        if buffer.endswith(b"\x00\x00"):
            log.warn(
                "Received an invalid OACK (multiple trailing nullbytes); will workaround: %r",
                buffer,
            )
            buffer = buffer.rstrip(b"\x00") + b"\x00"
            if len(buffer.split(b"\x00")) % 2 == 0:

                buffer += b"\x00"

        words = [x.decode("utf-8", "replace") for x in buffer.split(b"\x00")]
        if not words:
            log.debug("client provided no options")
            return {}

        tftpassert(words[-1] == "", "list of options is not null-terminated")
        words.pop()

        tftpassert(len(words) % 2 == 0, "packet has odd number of option/value pairs")

        options = {k: v for k, v in zip(words[::2], words[1::2])}
        for k in ("blksize", "tsize"):
            if k in options:
                options[k] = int(options[k])

        log.debug("options: %s", options.items())
        return options


class TftpPacket(object):
    "a"

    def __init__(self):
        self.opcode = 0
        self.buffer = None

    def encode(self):
        "a"
        raise NotImplementedError("Abstract method")

    def decode(self):
        "a"
        raise NotImplementedError("Abstract method")


class TftpPacketInitial(TftpPacket, TftpPacketWithOptions):
    "a"

    def __init__(self):
        TftpPacket.__init__(self)
        TftpPacketWithOptions.__init__(self)
        self.filename = None
        self.mode = None

    def encode(self):
        "a"
        tftpassert(self.filename, "filename required in initial packet")
        tftpassert(self.mode, "mode required in initial packet")

        filename = self.filename
        mode = self.mode
        if not isinstance(filename, bytes):
            filename = filename.encode("utf-8", "replace")
        if not isinstance(self.mode, bytes):
            mode = mode.encode("utf-8")

        ptype = None
        if self.opcode == 1:
            ptype = "RRQ"
        else:
            ptype = "WRQ"
        log.debug("Encoding %s packet, filename = %s, mode = %s", ptype, filename, mode)
        for key, value in self.options.items():
            log.debug("    Option %s = %s", key, value)

        fmt = b"!H"
        fmt += b"%dsx" % len(filename)
        if mode == b"octet":
            fmt += b"5sx"
        else:
            raise AssertionError("Unsupported mode: %s" % mode)

        opts = dict(self.options)
        if int(opts.get("blksize", 0)) == DEF_BLKSIZE:
            opts.pop("blksize")
        options_list = []
        if opts:
            log.debug("there are options to encode")
            for name, value in opts.items():

                if not isinstance(name, bytes):
                    name = name.encode("utf-8")
                options_list.append(name)
                fmt += b"%dsx" % len(name)

                if not isinstance(value, bytes):
                    value = str(value).encode("utf-8")
                options_list.append(value)
                fmt += b"%dsx" % len(value)

        log.debug("fmt is %s", fmt)
        log.debug("options_list is %s", options_list)
        log.debug("size of struct is %d", struct.calcsize(fmt))

        self.buffer = struct.pack(fmt, self.opcode, filename, mode, *options_list)

        log.debug("buffer is %s", repr(self.buffer))
        return self

    def decode(self):
        tftpassert(self.buffer, "Can't decode, buffer is empty")

        nulls = 0
        fmt = b""
        nulls = length = tlength = 0
        log.debug("in decode: about to iterate buffer counting nulls")
        subbuf = self.buffer[2:]
        for i in range(len(subbuf)):
            if ord(subbuf[i : i + 1]) == 0:
                nulls += 1
                log.debug("found a null at length %d, now have %d", length, nulls)
                fmt += b"%dsx" % length
                length = -1

                if nulls == 2:
                    break
            length += 1
            tlength += 1

        log.debug("hopefully found end of mode at length %d", tlength)

        tftpassert(nulls == 2, "malformed packet")
        shortbuf = subbuf[: tlength + 1]
        log.debug("unpacking %r using %s", shortbuf, fmt)
        mystruct = struct.unpack(fmt, shortbuf)

        tftpassert(len(mystruct) == 2, "malformed packet")
        self.filename = mystruct[0].decode("utf-8", "replace")
        self.mode = mystruct[1].decode("utf-8").lower()
        log.debug("set filename to %s", self.filename)
        log.debug("set mode to %s", self.mode)

        self.options = self.decode_options(subbuf[tlength + 1 :])
        log.debug("options dict is now %s", self.options)
        return self


class TftpPacketRRQ(TftpPacketInitial):
    "a"

    def __init__(self):
        TftpPacketInitial.__init__(self)
        self.opcode = 1

    def __str__(self):
        s = "RRQ packet: filename = %s" % self.filename
        s += " mode = %s" % self.mode
        if self.options:
            s += "\n    options = %s" % self.options
        return s


class TftpPacketWRQ(TftpPacketInitial):
    "a"

    def __init__(self):
        TftpPacketInitial.__init__(self)
        self.opcode = 2

    def __str__(self):
        s = "WRQ packet: filename = %s" % self.filename
        s += " mode = %s" % self.mode
        if self.options:
            s += "\n    options = %s" % self.options
        return s


class TftpPacketDAT(TftpPacket):
    "a"

    def __init__(self):
        TftpPacket.__init__(self)
        self.opcode = 3
        self.blocknumber = 0
        self.data = None

    def __str__(self):
        s = "DAT packet: block %s" % self.blocknumber
        if self.data:
            s += "\n    data: %d bytes" % len(self.data)
        return s

    def encode(self):
        "a"
        if not self.data:
            log.debug("Encoding an empty DAT packet")

        self.buffer = struct.pack(b"!HH", self.opcode, self.blocknumber) + self.data
        return self

    def decode(self):
        "a"

        (self.blocknumber,) = struct.unpack("!H", self.buffer[2:4])
        log.debug("decoding DAT packet, block number %d", self.blocknumber)
        log.debug("should be %d bytes in the packet total", len(self.buffer))

        self.data = self.buffer[4:]
        log.debug("found %d bytes of data", len(self.data))
        return self


class TftpPacketACK(TftpPacket):
    "a"

    def __init__(self):
        TftpPacket.__init__(self)
        self.opcode = 4
        self.blocknumber = 0

    def __str__(self):
        return "ACK packet: block %d" % self.blocknumber

    def encode(self):
        log.debug(
            "encoding ACK: opcode = %d, block = %d", self.opcode, self.blocknumber
        )
        self.buffer = struct.pack("!HH", self.opcode, self.blocknumber)
        return self

    def decode(self):
        if len(self.buffer) > 4:
            log.debug("detected TFTP ACK but request is too large, will truncate")
            log.debug("buffer was: %s", repr(self.buffer))
            self.buffer = self.buffer[0:4]
        self.opcode, self.blocknumber = struct.unpack("!HH", self.buffer)
        log.debug(
            "decoded ACK packet: opcode = %d, block = %d", self.opcode, self.blocknumber
        )
        return self


class TftpPacketERR(TftpPacket):
    "a"

    def __init__(self):
        TftpPacket.__init__(self)
        self.opcode = 5
        self.errorcode = 0

        self.errmsg = None

        self.errmsgs = {
            1: b"File not found",
            2: b"Access violation",
            3: b"Disk full or allocation exceeded",
            4: b"Illegal TFTP operation",
            5: b"Unknown transfer ID",
            6: b"File already exists",
            7: b"No such user",
            8: b"Failed to negotiate options",
        }

    def __str__(self):
        s = "ERR packet: errorcode = %d" % self.errorcode
        s += "\n    msg = %s" % self.errmsgs.get(self.errorcode, "")
        return s

    def encode(self):
        "a"
        fmt = b"!HH%dsx" % len(self.errmsgs[self.errorcode])
        log.debug("encoding ERR packet with fmt %s", fmt)
        self.buffer = struct.pack(
            fmt, self.opcode, self.errorcode, self.errmsgs[self.errorcode]
        )
        return self

    def decode(self):
        "a"
        buflen = len(self.buffer)
        tftpassert(buflen >= 4, "malformed ERR packet, too short")
        log.debug("Decoding ERR packet, length %s bytes", buflen)
        if buflen == 4:
            log.debug("Allowing this affront to the RFC of a 4-byte packet")
            fmt = b"!HH"
            log.debug("Decoding ERR packet with fmt: %s", fmt)
            self.opcode, self.errorcode = struct.unpack(fmt, self.buffer)
        else:
            log.debug("Good ERR packet > 4 bytes")
            fmt = b"!HH%dsx" % (len(self.buffer) - 5)
            log.debug("Decoding ERR packet with fmt: %s", fmt)
            self.opcode, self.errorcode, self.errmsg = struct.unpack(fmt, self.buffer)
        log.error(
            "ERR packet - errorcode: %d, message: %s", self.errorcode, self.errmsg
        )
        return self


class TftpPacketOACK(TftpPacket, TftpPacketWithOptions):
    "a"

    def __init__(self):
        TftpPacket.__init__(self)
        TftpPacketWithOptions.__init__(self)
        self.opcode = 6

    def __str__(self):
        return "OACK packet:\n    options = %s" % self.options

    def encode(self):
        fmt = b"!H"
        options_list = []
        log.debug("in TftpPacketOACK.encode")
        for key, value in self.options.items():
            if not isinstance(key, bytes):
                key = key.encode("utf-8")
            if not isinstance(value, bytes):
                value = str(value).encode("utf-8")
            log.debug("looping on option key %s", key)
            log.debug("value is %s", value)
            fmt += b"%dsx" % len(key)
            fmt += b"%dsx" % len(value)
            options_list.append(key)
            options_list.append(value)
        self.buffer = struct.pack(fmt, self.opcode, *options_list)
        return self

    def decode(self):
        self.options = self.decode_options(self.buffer[2:])
        return self

    def match_options(self, options):
        "a"
        for name, value in self.options.items():
            if name not in options:
                continue

            if name == "blksize":

                size = int(value)
                if size >= MIN_BLKSIZE and size <= MAX_BLKSIZE:
                    log.debug("negotiated blksize of %d bytes", size)
                    options["blksize"] = size
                else:
                    raise TftpException(
                        "blksize %s option outside allowed range" % size
                    )
            elif name == "tsize":
                size = int(value)
                if size < 0:
                    raise TftpException("Negative file sizes not supported")
            else:
                raise TftpException("Unsupported option: %s" % name)
        return True
