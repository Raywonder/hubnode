# coding: utf-8
# vim: ts=4 sw=4 et ai:
from __future__ import print_function, unicode_literals

"a"


import logging
import os
import socket
import sys
import time

from .TftpPacketFactory import TftpPacketFactory
from .TftpPacketTypes import *
from .TftpShared import *
from .TftpStates import *

if TYPE_CHECKING:
    from typing import Optional

log = logging.getLogger("partftpy.TftpContext")



class TftpMetrics(object):
    "a"

    def __init__(self):

        self.tsize = 0

        self.bytes = 0
        self.packets = 0
        self.resent_bytes = 0
        self.resent_packets = 0

        self.dups = {}
        self.dupcount = 0

        self.start_time = 0
        self.end_time = 0
        self.duration = 0
        self.last_dat_time = 0

        self.bps = 0
        self.kbps = 0

        self.errors = 0

    def compute(self):

        self.duration = self.end_time - self.start_time
        if self.duration == 0:
            self.duration = 1
        self.bps = (self.bytes * 8.0) / self.duration
        self.kbps = self.bps / 1024.0
        spd = self.kbps / 8192.0
        log.debug("TftpMetrics.compute: %ss, %.4f MiB/s", self.duration, spd)
        for key in self.dups:
            self.dupcount += self.dups[key]

    def add_dup(self, pkt):
        "a"
        log.debug("Recording a dup of %s", pkt)
        s = str(pkt)
        if s in self.dups:
            self.dups[s] += 1
        else:
            self.dups[s] = 1
        tftpassert(self.dups[s] < MAX_DUPS, "Max duplicates reached")



class TftpContext(object):
    "a"

    def __init__(
        self,
        host,
        port,
        timeout,
        retries=DEF_TIMEOUT_RETRIES,
        localip="",
        af_family=socket.AF_INET,
        ports=None,
    ):
        "a"
        self.file_to_transfer = None
        self.fileobj = None
        self.options = None
        self.packethook = None
        self.af_family = af_family
        self.sock = socket.socket(af_family, socket.SOCK_DGRAM)
        if not localip:
            localip = "0.0.0.0" if af_family == socket.AF_INET else "::"

        for n in ports or [0]:
            try:
                self.sock.bind((localip, n))
                break
            except:
                continue
        log.info("will reply from %s:", self.sock.getsockname())

        self.sock.settimeout(timeout)
        self.timeout = timeout
        self.retries = retries
        self.state = None
        self.next_block = 0
        self.factory = TftpPacketFactory()

        self.address = ""
        self.address4 = ""
        self.host = host
        self.port = port

        self.tidport = None

        self.metrics = TftpMetrics()

        self.pending_complete = False

        self.last_update = 0

        self.last_pkt = None

        self.retry_count = 0

        self.timeout_expectACK = False

    def __del__(self):
        "a"
        self.end()

    def checkTimeout(self, now):
        "a"
        log.debug("checking for timeout on session %s", self)
        if self.timeout_expectACK:
            raise TftpTimeout("Timeout waiting for traffic")
        if now - self.last_update > self.timeout:
            raise TftpTimeout("Timeout waiting for traffic")

    def start(self):
        raise NotImplementedError("Abstract method")

    def end(self, close_fileobj=True):
        "a"
        log.debug("in TftpContext.end - closing socket")
        self.sock.close()
        if close_fileobj and self.fileobj is not None and not self.fileobj.closed:
            log.debug("self.fileobj is open - closing")
            self.fileobj.close()

    def gethost(self):
        "a"
        return self.__host

    def sethost(self, host):
        "a"
        self.__host = host
        if self.af_family == socket.AF_INET:
            self.address = socket.gethostbyname(host)
        elif self.af_family == socket.AF_INET6:
            self.address = socket.getaddrinfo(host, 0)[0][4][0]
        else:
            raise ValueError("af_family is not supported")

        if self.address.startswith("::ffff:"):
            self.address4 = self.address[7:]
        else:
            self.address4 = self.address

    host = property(gethost, sethost)

    def setNextBlock(self, block):
        if block >= 2 ** 16:
            log.debug("Block number rollover to 0 again")
            block = 0
        self.__eblock = block

    def getNextBlock(self):
        return self.__eblock

    next_block = property(getNextBlock, setNextBlock)

    def cycle(self):
        "a"
        try:
            buffer, rai = self.sock.recvfrom(MAX_BLKSIZE)
            raddress = rai[0]
            rport = rai[1]
        except socket.timeout:
            log.warning("Timeout waiting for traffic, retrying...")
            raise TftpTimeout("Timed-out waiting for traffic")

        log.debug("Received %d bytes from %s:%s", len(buffer), raddress, rport)

        self.last_update = time.time()

        recvpkt = self.factory.parse(buffer)

        if (
            raddress != self.address
            and raddress != self.address4
            and raddress.lstrip(":f") != self.address4
        ):
            log.warning(
                "Received traffic from %s, expected host %s. Discarding",
                raddress,
                self.host,
            )

        if self.tidport and self.tidport != rport:
            log.warning(
                "Received traffic from %s:%s but we're connected to %s:%s. Discarding.",
                raddress,
                rport,
                self.host,
                self.tidport,
            )

        if self.packethook:
            self.packethook(recvpkt, self)

        self.state = self.state.handle(recvpkt, raddress, rport)

        self.retry_count = 0


class TftpContextServer(TftpContext):
    "a"

    def __init__(
        self,
        host,
        port,
        timeout,
        root,
        dyn_file_func=None,
        upload_open=None,
        retries=DEF_TIMEOUT_RETRIES,
        af_family=socket.AF_INET,
        ports=None,
    ):
        TftpContext.__init__(
            self, host, port, timeout, retries, af_family=af_family, ports=ports
        )

        self.state = TftpStateServerStart(self)

        self.root = root
        self.dyn_file_func = dyn_file_func
        self.upload_open = upload_open

    def __str__(self):
        return "%s:%s %s" % (self.host, self.port, self.state)

    def start(self, buffer):
        "a"
        log.debug("In TftpContextServer.start")
        self.metrics.start_time = time.time()
        log.debug("Set metrics.start_time to %s", self.metrics.start_time)

        self.last_update = time.time()

        pkt = self.factory.parse(buffer)
        log.debug("TftpContextServer.start() - factory returned a %s", pkt)

        self.state = self.state.handle(pkt, self.host, self.port)

    def end(self):
        "a"
        TftpContext.end(self)
        self.metrics.end_time = time.time()
        log.debug("Set metrics.end_time to %s", self.metrics.end_time)
        log.debug("Detected dups in transfer: %d", self.metrics.dupcount)
        self.metrics.compute()


class TftpContextClientUpload(TftpContext):
    "a"

    def __init__(
        self,
        host,
        port,
        filename,
        input,
        options,
        packethook,
        timeout,
        retries=DEF_TIMEOUT_RETRIES,
        localip="",
        af_family=socket.AF_INET,
        ports=None,
    ):
        TftpContext.__init__(
            self, host, port, timeout, retries, localip, af_family, ports
        )
        self.file_to_transfer = filename
        self.options = options
        self.packethook = packethook

        if hasattr(input, "read"):
            self.fileobj = input
        elif input == "-":
            self.fileobj = sys.stdin if PY2 else sys.stdin.buffer
        else:
            self.fileobj = open(input, "rb")

        log.debug("TftpContextClientUpload.__init__()")
        log.debug(
            "file_to_transfer = %s, options = %s", self.file_to_transfer, self.options
        )

    def __str__(self):
        return "%s:%s %s" % (self.host, self.port, self.state)

    def start(self):
        log.info("Sending tftp upload request to %s", self.host)
        log.info("    filename -> %s", self.file_to_transfer)
        log.info("    options -> %s", self.options)

        tsize = self.options.get("tsize")
        if tsize:
            self.metrics.tsize = tsize

        self.metrics.start_time = time.time()
        log.debug("Set metrics.start_time to %s", self.metrics.start_time)

        pkt = TftpPacketWRQ()
        pkt.filename = self.file_to_transfer
        pkt.mode = "octet"
        pkt.options = self.options
        self.sock.sendto(pkt.encode().buffer, (self.host, self.port))
        self.next_block = 1
        self.last_pkt = pkt


        self.state = TftpStateSentWRQ(self)

        while self.state:
            try:
                log.debug("State is %s", self.state)
                self.cycle()
            except TftpTimeout as err:
                log.error(str(err))
                self.retry_count += 1
                if self.retry_count >= self.retries:
                    log.debug("hit max retries, giving up")
                    raise
                else:
                    log.warning("resending last packet")
                    self.state.resendLast()

    def end(self):
        "a"
        TftpContext.end(self)
        self.metrics.end_time = time.time()
        log.debug("Set metrics.end_time to %s", self.metrics.end_time)
        self.metrics.compute()


class TftpContextClientDownload(TftpContext):
    "a"

    def __init__(
        self,
        host,
        port,
        filename,
        output,
        options,
        packethook,
        timeout,
        retries=DEF_TIMEOUT_RETRIES,
        localip="",
        af_family=socket.AF_INET,
        ports=None,
    ):
        TftpContext.__init__(
            self, host, port, timeout, retries, localip, af_family, ports
        )

        self.file_to_transfer = filename
        self.options = options
        self.packethook = packethook
        self.filelike_fileobj = False

        if hasattr(output, "write"):
            self.fileobj = output
            self.filelike_fileobj = True

        elif output == "-":
            self.fileobj = sys.stdout if PY2 else sys.stdout.buffer
            self.filelike_fileobj = True
        else:
            self.fileobj = open(output, "wb")

        log.debug("TftpContextClientDownload.__init__()")
        log.debug(
            "file_to_transfer = %s, options = %s", self.file_to_transfer, self.options
        )

    def __str__(self):
        return "%s:%s %s" % (self.host, self.port, self.state)

    def start(self):
        "a"
        log.info("Sending tftp download request to %s", self.host)
        log.info("    filename -> %s", self.file_to_transfer)
        log.info("    options -> %s", self.options)

        self.metrics.start_time = time.time()
        log.debug("Set metrics.start_time to %s", self.metrics.start_time)

        pkt = TftpPacketRRQ()
        pkt.filename = self.file_to_transfer
        pkt.mode = "octet"
        pkt.options = self.options
        self.sock.sendto(pkt.encode().buffer, (self.host, self.port))
        self.next_block = 1
        self.last_pkt = pkt

        self.state = TftpStateSentRRQ(self)

        while self.state:
            try:
                log.debug("State is %s", self.state)
                self.cycle()
            except TftpTimeout as err:
                log.error(str(err))
                self.retry_count += 1
                if self.retry_count >= self.retries:
                    log.debug("hit max retries, giving up")
                    raise
                else:
                    log.warning("resending last packet")
                    self.state.resendLast()
            except TftpFileNotFoundError:

                log.error("Received File not found error")
                if self.fileobj is not None and not self.filelike_fileobj:
                    if os.path.exists(self.fileobj.name):
                        log.debug("unlinking output file of %s", self.fileobj.name)
                        os.unlink(self.fileobj.name)

                raise

    def end(self):
        "a"
        TftpContext.end(self, not self.filelike_fileobj)
        self.metrics.end_time = time.time()
        log.debug("Set metrics.end_time to %s", self.metrics.end_time)
        self.metrics.compute()
