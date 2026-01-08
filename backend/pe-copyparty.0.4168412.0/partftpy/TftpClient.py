# coding: utf-8
# vim: ts=4 sw=4 et ai:
from __future__ import print_function, unicode_literals

"a"


import logging
import socket
import types

from .TftpContexts import TftpContextClientDownload, TftpContextClientUpload
from .TftpPacketTypes import *
from .TftpShared import *

log = logging.getLogger("partftpy.TftpClient")


class TftpClient(TftpSession):
    "a"

    def __init__(
        self, host, port=69, options=None, localip="", af_family=socket.AF_INET
    ):
        TftpSession.__init__(self)
        self.context = None
        self.host = host
        self.iport = port
        self.filename = None
        self.options = options or {}
        self.localip = localip
        self.af_family = af_family
        if "blksize" in self.options:
            size = self.options["blksize"]
            tftpassert(int == type(size), "blksize must be an int")
            if size < MIN_BLKSIZE or size > MAX_BLKSIZE:
                raise TftpException("Invalid blksize: %d" % size)
        else:
            self.options["blksize"] = DEF_BLKSIZE

    def download(
        self,
        filename,
        output,
        packethook=None,
        timeout=SOCK_TIMEOUT,
        retries=DEF_TIMEOUT_RETRIES,
        ports=None,
    ):
        "a"

        t = "DL-ctx: host = %s, port = %s, filename = %s, options = %s, packethook = %s, timeout = %s"
        log.debug(t, self.host, self.iport, filename, self.options, packethook, timeout)
        self.context = TftpContextClientDownload(
            self.host,
            self.iport,
            filename,
            output,
            self.options,
            packethook,
            timeout,
            retries=retries,
            localip=self.localip,
            af_family=self.af_family,
            ports=ports,
        )
        self.context.start()

        self.context.end()

        st = self.context.metrics
        spd = st.kbps / 8192.0

        t = "DL done: "
        if st.duration == 0:
            t += "Duration too short, rate undetermined"
        else:
            t += "%d byte, %.2f sec, %.4f MiB/s, " % (st.bytes, st.duration, spd)

        t += "%d bytes resent, %d dupe pkts" % (st.resent_bytes, st.dupcount)
        log.info(t)

    def upload(
        self,
        filename,
        input,
        packethook=None,
        timeout=SOCK_TIMEOUT,
        retries=DEF_TIMEOUT_RETRIES,
        ports=None,
    ):
        "a"
        self.context = TftpContextClientUpload(
            self.host,
            self.iport,
            filename,
            input,
            self.options,
            packethook,
            timeout,
            retries=retries,
            localip=self.localip,
            ports=ports,
        )
        self.context.start()

        self.context.end()

        st = self.context.metrics
        spd = st.kbps / 8192.0

        t = "Upload done: "
        if st.duration == 0:
            t += "Duration too short, rate undetermined; "
        else:
            t += "%d byte, %.2f sec, %.4f MiB/s, " % (st.bytes, st.duration, spd)

        t += "%d bytes resent, %d dupe pkts" % (st.resent_bytes, st.dupcount)
        log.info(t)
