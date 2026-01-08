# coding: utf-8
# vim: ts=4 sw=4 et ai:
from __future__ import print_function, unicode_literals

"a"


import logging
import os
import select
import socket
import threading
import time
from errno import EINTR

from .TftpContexts import TftpContextServer
from .TftpPacketFactory import TftpPacketFactory
from .TftpPacketTypes import *
from .TftpShared import *

log = logging.getLogger("partftpy.TftpServer")


class TftpServer(TftpSession):
    "a"

    def __init__(self, tftproot="/tftpboot", dyn_file_func=None, upload_open=None):
        self.listenip = None
        self.listenport = None
        self.sock = None

        self.root = os.path.abspath(tftproot)
        self.dyn_file_func = dyn_file_func
        self.upload_open = upload_open

        self.sessions = {}

        self.is_running = threading.Event()

        self.shutdown_gracefully = False
        self.shutdown_immediately = False

        for name in "dyn_file_func", "upload_open":
            attr = getattr(self, name)
            if attr and not callable(attr):
                raise TftpException("%s supplied, but it is not callable." % (name,))
        if os.path.exists(self.root):
            log.debug("tftproot %s does exist", self.root)
            if not os.path.isdir(self.root):
                raise TftpException("The tftproot must be a directory.")
            else:
                log.debug("tftproot %s is a directory", self.root)
                if os.access(self.root, os.R_OK):
                    log.debug("tftproot %s is readable", self.root)
                else:
                    raise TftpException("The tftproot must be readable")
                if os.access(self.root, os.W_OK):
                    log.debug("tftproot %s is writable", self.root)
                else:
                    log.warning("The tftproot %s is not writable", self.root)
        else:
            raise TftpException("The tftproot does not exist.")

    def listen(
        self,
        listenip="",
        listenport=DEF_TFTP_PORT,
        timeout=SOCK_TIMEOUT,
        retries=DEF_TIMEOUT_RETRIES,
        af_family=socket.AF_INET,
        ports=None,
    ):
        "a"

        if not listenip:
            listenip = "0.0.0.0" if af_family == socket.AF_INET else "::"

        ip_str = listenip if af_family == socket.AF_INET else "[%s]" % (listenip,)
        try:

            self.sock = socket.socket(af_family, socket.SOCK_DGRAM)
            self.sock.bind((listenip, listenport))
            self.listenport = self.sock.getsockname()[1]
        except OSError as err:

            raise err

        log.info("listening @ %s:%s", ip_str, listenport)
        self.is_running.set()
        last_timeout_chk = 0

        log.debug("Starting receive loop...")
        while True:
            log.debug("shutdown_immediately is %s", self.shutdown_immediately)
            log.debug("shutdown_gracefully is %s", self.shutdown_gracefully)
            if self.shutdown_immediately:
                log.info("Shutting down now. Session count: %d", len(self.sessions))
                self.sock.close()
                for key in self.sessions:
                    log.warning(
                        "Forcefully closed session with %s", self.sessions[key].host
                    )
                    self.sessions[key].end()
                self.sessions = []
                break

            elif self.shutdown_gracefully:
                if not self.sessions:
                    log.info("In graceful shutdown mode and all sessions complete.")
                    self.sock.close()
                    break

            inputlist = [self.sock]
            for key in self.sessions:
                inputlist.append(self.sessions[key].sock)

            log.debug("Performing select on this inputlist: %s", inputlist)
            try:
                readyinput, readyoutput, readyspecial = select.select(
                    inputlist, [], [], timeout
                )
            except OSError as err:
                if err[0] == EINTR:

                    log.debug("Interrupted syscall, retrying")
                    continue
                else:
                    raise

            deletion_list = []

            for readysock in readyinput:

                if readysock == self.sock:
                    log.debug("Data ready on our main socket")
                    buffer, rai = self.sock.recvfrom(MAX_BLKSIZE)
                    raddress = rai[0]
                    rport = rai[1]

                    log.debug("Read %d bytes", len(buffer))

                    if self.shutdown_gracefully:
                        log.warning(
                            "Discarding data on main port, in graceful shutdown mode"
                        )
                        continue

                    key = "%s:%s" % (raddress, rport)

                    if key not in self.sessions:
                        log.debug(
                            "Creating new server context for session key = %s", key
                        )
                        self.sessions[key] = TftpContextServer(
                            raddress,
                            rport,
                            timeout,
                            self.root,
                            self.dyn_file_func,
                            self.upload_open,
                            retries=retries,
                            af_family=af_family,
                            ports=ports,
                        )
                        try:
                            self.sessions[key].start(buffer)
                        except TftpTimeoutExpectACK:
                            self.sessions[key].timeout_expectACK = True
                        except Exception as err:
                            zb = isinstance(err, TftpException)
                            if zb and str(err).startswith("File not found:"):
                                pass
                            else:
                                self.sessions[key].state.sendError(
                                    TftpErrors.AccessViolation
                                )

                            deletion_list.append(key)
                            log.error(
                                "Fatal exception thrown from session %s: %s",
                                key,
                                str(err),
                            )
                    else:
                        log.warning(
                            "received traffic on main socket for existing session??"
                        )
                    t = "Active sessions:"
                    for session_key, session in list(self.sessions.items()):
                        t += "\n  %s" % (session,)
                    log.info(t)

                else:

                    for key in self.sessions:
                        if readysock == self.sessions[key].sock:
                            log.debug("Matched input to session key %s", key)
                            self.sessions[key].timeout_expectACK = False
                            try:
                                self.sessions[key].cycle()
                                if self.sessions[key].state is None:
                                    log.debug("Successful transfer.")
                                    deletion_list.append(key)
                            except TftpTimeoutExpectACK:
                                self.sessions[key].timeout_expectACK = True
                            except Exception as err:
                                zb = isinstance(err, TftpException)
                                if zb and str(err).startswith("File not found:"):
                                    pass
                                else:
                                    self.sessions[key].state.sendError(
                                        TftpErrors.AccessViolation
                                    )

                                self.sessions[key].state.sendError(
                                    TftpErrors.AccessViolation
                                )
                                deletion_list.append(key)
                                log.error(
                                    "Fatal exception thrown from session %s: %s",
                                    key,
                                    str(err),
                                )

                            break
                    else:
                        log.error("Can't find the owner for this packet. Discarding.")

            now = time.time()
            if now - last_timeout_chk > 0.1:
                last_timeout_chk = now
                log.debug("Looping on all sessions to check for timeouts")
                for key in self.sessions:
                    try:
                        self.sessions[key].checkTimeout(now)
                    except TftpTimeout as err:
                        log.error(str(err))
                        self.sessions[key].retry_count += 1
                        if self.sessions[key].retry_count >= self.sessions[key].retries:
                            log.debug(
                                "hit max retries on %s, giving up", self.sessions[key]
                            )
                            deletion_list.append(key)
                        else:
                            log.debug("resending on session %s", self.sessions[key])
                            self.sessions[key].state.resendLast()

            log.debug("Iterating deletion list.")
            for key in deletion_list:
                log.debug("Session %s complete", key)
                t = "%s done: " % (key,)
                if key in self.sessions:
                    log.debug("Gathering up metrics from session before deleting")
                    self.sessions[key].end()
                    st = self.sessions[key].metrics
                    spd = st.kbps / 8192.0
                    if st.duration == 0:
                        t += "Duration too short, rate undetermined; "
                    else:
                        t += "%d byte, %.2f sec, %.4f MiB/s, " % (
                            st.bytes,
                            st.duration,
                            spd,
                        )

                    t += "%d bytes resent, %d dupe pkts" % (
                        st.resent_bytes,
                        st.dupcount,
                    )
                    log.info(t)

                    log.debug("Deleting session %s", key)
                    del self.sessions[key]
                    log.debug("Session list is now %s", self.sessions)
                else:
                    log.warning("Strange, session %s is not on the deletion list", key)

        self.is_running.clear()

        log.debug("server returning from while loop")
        self.shutdown_gracefully = self.shutdown_immediately = False

    def stop(self, now=False):
        "a"
        if now:
            self.shutdown_immediately = True
        else:
            self.shutdown_gracefully = True
