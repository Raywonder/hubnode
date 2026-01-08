# Copyright (C) 2007 Giampaolo Rodola' <g.rodola@gmail.com>.
# Use of this source code is governed by MIT license that can be
# found in the LICENSE file.

import contextlib
import errno
import glob
import logging
import os
import random
import socket
import sys
import time
import traceback
import warnings
from datetime import datetime


try:
    import grp
    import pwd
except ImportError:
    pwd = grp = None

try:
    from OpenSSL import SSL
except ImportError:
    SSL = None

try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict

from . import __ver__
from ._compat import PY3
from ._compat import PermissionError
from ._compat import b
from ._compat import getcwdu
from ._compat import super
from ._compat import u
from ._compat import unicode
from ._compat import xrange
from .authorizers import AuthenticationFailed
from .authorizers import AuthorizerError
from .authorizers import DummyAuthorizer
from .filesystems import AbstractedFS
from .filesystems import FilesystemError
from .ioloop import _ERRNOS_DISCONNECTED
from .ioloop import _ERRNOS_RETRY
from .ioloop import Acceptor
from .ioloop import AsyncChat
from .ioloop import Connector
from .ioloop import RetryError
from .ioloop import timer
from .log import debug
from .log import logger


if PY3:
    from . import _asynchat as asynchat
else:
    import asynchat


CR_BYTE = ord('\r')


def _import_sendfile():

    if os.name == 'posix':
        try:
            return os.sendfile
        except AttributeError:
            try:
                import sendfile as sf

                if hasattr(sf, 'has_sf_hdtr'):
                    raise ImportError
                return sf.sendfile
            except ImportError:
                pass
    return None


sendfile = _import_sendfile()

proto_cmds = {
    'ABOR': dict(
        perm=None, auth=True, arg=False, help='Syntax: ABOR (abort transfer).'
    ),
    'ALLO': dict(
        perm=None,
        auth=True,
        arg=True,
        help='Syntax: ALLO <SP> bytes (noop; allocate storage).',
    ),
    'APPE': dict(
        perm='a',
        auth=True,
        arg=True,
        help='Syntax: APPE <SP> file-name (append data to file).',
    ),
    'CDUP': dict(
        perm='e',
        auth=True,
        arg=False,
        help='Syntax: CDUP (go to parent directory).',
    ),
    'CWD': dict(
        perm='e',
        auth=True,
        arg=None,
        help='Syntax: CWD [<SP> dir-name] (change working directory).',
    ),
    'DELE': dict(
        perm='d',
        auth=True,
        arg=True,
        help='Syntax: DELE <SP> file-name (delete file).',
    ),
    'EPRT': dict(
        perm=None,
        auth=True,
        arg=True,
        help='Syntax: EPRT <SP> |proto|ip|port| (extended active mode).',
    ),
    'EPSV': dict(
        perm=None,
        auth=True,
        arg=None,
        help='Syntax: EPSV [<SP> proto/"ALL"] (extended passive mode).',
    ),
    'FEAT': dict(
        perm=None,
        auth=False,
        arg=False,
        help='Syntax: FEAT (list all new features supported).',
    ),
    'HELP': dict(
        perm=None,
        auth=False,
        arg=None,
        help='Syntax: HELP [<SP> cmd] (show help).',
    ),
    'LIST': dict(
        perm='l',
        auth=True,
        arg=None,
        help='Syntax: LIST [<SP> path] (list files).',
    ),
    'MDTM': dict(
        perm='l',
        auth=True,
        arg=True,
        help='Syntax: MDTM [<SP> path] (file last modification time).',
    ),
    'MFMT': dict(
        perm='T',
        auth=True,
        arg=True,
        help=(
            'Syntax: MFMT <SP> timeval <SP> path (file update last '
            'modification time).'
        ),
    ),
    'MLSD': dict(
        perm='l',
        auth=True,
        arg=None,
        help='Syntax: MLSD [<SP> path] (list directory).',
    ),
    'MLST': dict(
        perm='l',
        auth=True,
        arg=None,
        help='Syntax: MLST [<SP> path] (show information about path).',
    ),
    'MODE': dict(
        perm=None,
        auth=True,
        arg=True,
        help='Syntax: MODE <SP> mode (noop; set data transfer mode).',
    ),
    'MKD': dict(
        perm='m',
        auth=True,
        arg=True,
        help='Syntax: MKD <SP> path (create directory).',
    ),
    'NLST': dict(
        perm='l',
        auth=True,
        arg=None,
        help='Syntax: NLST [<SP> path] (list path in a compact form).',
    ),
    'NOOP': dict(
        perm=None,
        auth=False,
        arg=False,
        help='Syntax: NOOP (just do nothing).',
    ),
    'OPTS': dict(
        perm=None,
        auth=True,
        arg=True,
        help='Syntax: OPTS <SP> cmd [<SP> option] (set option for command).',
    ),
    'PASS': dict(
        perm=None,
        auth=False,
        arg=None,
        help='Syntax: PASS [<SP> password] (set user password).',
    ),
    'PASV': dict(
        perm=None,
        auth=True,
        arg=False,
        help='Syntax: PASV (open passive data connection).',
    ),
    'PORT': dict(
        perm=None,
        auth=True,
        arg=True,
        help='Syntax: PORT <sp> h,h,h,h,p,p (open active data connection).',
    ),
    'PWD': dict(
        perm=None,
        auth=True,
        arg=False,
        help='Syntax: PWD (get current working directory).',
    ),
    'QUIT': dict(
        perm=None,
        auth=False,
        arg=False,
        help='Syntax: QUIT (quit current session).',
    ),
    'REIN': dict(
        perm=None, auth=True, arg=False, help='Syntax: REIN (flush account).'
    ),
    'REST': dict(
        perm=None,
        auth=True,
        arg=True,
        help='Syntax: REST <SP> offset (set file offset).',
    ),
    'RETR': dict(
        perm='r',
        auth=True,
        arg=True,
        help='Syntax: RETR <SP> file-name (retrieve a file).',
    ),
    'RMD': dict(
        perm='d',
        auth=True,
        arg=True,
        help='Syntax: RMD <SP> dir-name (remove directory).',
    ),
    'RNFR': dict(
        perm='f',
        auth=True,
        arg=True,
        help='Syntax: RNFR <SP> file-name (rename (source name)).',
    ),
    'RNTO': dict(
        perm='f',
        auth=True,
        arg=True,
        help='Syntax: RNTO <SP> file-name (rename (destination name)).',
    ),
    'SITE': dict(
        perm=None,
        auth=False,
        arg=True,
        help='Syntax: SITE <SP> site-command (execute SITE command).',
    ),
    'SITE HELP': dict(
        perm=None,
        auth=False,
        arg=None,
        help='Syntax: SITE HELP [<SP> cmd] (show SITE command help).',
    ),
    'SITE CHMOD': dict(
        perm='M',
        auth=True,
        arg=True,
        help='Syntax: SITE CHMOD <SP> mode path (change file mode).',
    ),
    'SIZE': dict(
        perm='l',
        auth=True,
        arg=True,
        help='Syntax: SIZE <SP> file-name (get file size).',
    ),
    'STAT': dict(
        perm='l',
        auth=False,
        arg=None,
        help='Syntax: STAT [<SP> path name] (server stats [list files]).',
    ),
    'STOR': dict(
        perm='w',
        auth=True,
        arg=True,
        help='Syntax: STOR <SP> file-name (store a file).',
    ),
    'STOU': dict(
        perm='w',
        auth=True,
        arg=None,
        help='Syntax: STOU [<SP> name] (store a file with a unique name).',
    ),
    'STRU': dict(
        perm=None,
        auth=True,
        arg=True,
        help='Syntax: STRU <SP> type (noop; set file structure).',
    ),
    'SYST': dict(
        perm=None,
        auth=False,
        arg=False,
        help='Syntax: SYST (get operating system type).',
    ),
    'TYPE': dict(
        perm=None,
        auth=True,
        arg=True,
        help='Syntax: TYPE <SP> [A | I] (set transfer type).',
    ),
    'USER': dict(
        perm=None,
        auth=False,
        arg=True,
        help='Syntax: USER <SP> user-name (set username).',
    ),
    'XCUP': dict(
        perm='e',
        auth=True,
        arg=False,
        help='Syntax: XCUP (obsolete; go to parent directory).',
    ),
    'XCWD': dict(
        perm='e',
        auth=True,
        arg=None,
        help='Syntax: XCWD [<SP> dir-name] (obsolete; change directory).',
    ),
    'XMKD': dict(
        perm='m',
        auth=True,
        arg=True,
        help='Syntax: XMKD <SP> dir-name (obsolete; create directory).',
    ),
    'XPWD': dict(
        perm=None,
        auth=True,
        arg=False,
        help='Syntax: XPWD (obsolete; get current dir).',
    ),
    'XRMD': dict(
        perm='d',
        auth=True,
        arg=True,
        help='Syntax: XRMD <SP> dir-name (obsolete; remove directory).',
    ),
}

if not hasattr(os, 'chmod'):
    del proto_cmds['SITE CHMOD']


def _strerror(err):
    if isinstance(err, EnvironmentError):
        try:
            return os.strerror(err.errno)
        except AttributeError:

            if not hasattr(os, 'strerror'):
                return err.strerror
            raise
    else:
        return str(err)


def _is_ssl_sock(sock):
    return SSL is not None and isinstance(sock, SSL.Connection)


def _support_hybrid_ipv6():
    "a"

    try:
        if not socket.has_ipv6:
            return False
        with contextlib.closing(socket.socket(socket.AF_INET6)) as sock:
            return not sock.getsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY)
    except (socket.error, AttributeError):
        return False


SUPPORTS_HYBRID_IPV6 = _support_hybrid_ipv6()


class _FileReadWriteError(OSError):
    "a"


class _GiveUpOnSendfile(Exception):
    "a"



class PassiveDTP(Acceptor):
    "a"

    timeout = 30
    backlog = None

    def __init__(self, cmd_channel, extmode=False):
        "a"
        self.cmd_channel = cmd_channel
        self.log = cmd_channel.log
        self.log_exception = cmd_channel.log_exception
        Acceptor.__init__(self, ioloop=cmd_channel.ioloop)

        sockname = list(self.cmd_channel.socket.getsockname())
        local_ip = sockname[0]
        if local_ip in self.cmd_channel.masquerade_address_map:
            masqueraded_ip = self.cmd_channel.masquerade_address_map[local_ip]
        elif self.cmd_channel.masquerade_address:
            masqueraded_ip = self.cmd_channel.masquerade_address
        else:
            masqueraded_ip = None

        if local_ip.startswith('fe') and local_ip[2:3] in "89ab":
            af = socket.AF_INET6
        elif self.cmd_channel.server.socket.family != socket.AF_INET:

            af = self.bind_af_unspecified((local_ip, 0))
            self.socket.close()
            self.del_channel()
        else:
            af = self.cmd_channel.socket.family

        self.create_socket(af, socket.SOCK_STREAM)

        if self.cmd_channel.passive_ports is None:

            sockname[1] = 0
            self.bind(tuple(sockname))
        else:
            ports = list(self.cmd_channel.passive_ports)
            while ports:
                port = ports.pop(random.randint(0, len(ports) - 1))
                self.set_reuse_addr()
                sockname[1] = port
                try:
                    self.bind(tuple(sockname))
                except PermissionError:
                    self.cmd_channel.log(
                        "ignoring EPERM when bind()ing port %s" % port,
                        logfun=logger.debug,
                    )
                except socket.error as err:
                    if err.errno == errno.EADDRINUSE:
                        if ports:
                            continue

                        else:
                            sockname[1] = 0
                            self.bind(tuple(sockname))
                            self.cmd_channel.log(
                                "Can't find a valid passive port in the "
                                "configured range. A random kernel-assigned "
                                "port will be used.",
                                logfun=logger.warning,
                            )
                    else:
                        raise
                else:
                    break
        self.listen(self.backlog or self.cmd_channel.server.backlog)

        port = self.socket.getsockname()[1]
        if not extmode:
            ip = masqueraded_ip or local_ip
            if ip.startswith('::ffff:'):

                ip = ip[7:]

            resp = '227 Entering passive mode (%s,%d,%d).' % (
                ip.replace('.', ','),
                port // 256,
                port % 256,
            )
            self.cmd_channel.respond(resp)
        else:
            self.cmd_channel.respond(
                '229 Entering extended passive mode (|||%d|).' % port
            )
        if self.timeout:
            self.call_later(self.timeout, self.handle_timeout)


    def handle_accepted(self, sock, addr):
        "a"
        if not self.cmd_channel.connected:
            return self.close()

        if self.cmd_channel.remote_ip != addr[0]:
            if not self.cmd_channel.permit_foreign_addresses:
                try:
                    sock.close()
                except socket.error:
                    pass
                msg = (
                    '425 Rejected data connection from foreign address '
                    + '%s:%s.' % (addr[0], addr[1])
                )
                self.cmd_channel.respond_w_warning(msg)

                return
            else:

                msg = (
                    'Established data connection with foreign address '
                    + '%s:%s.' % (addr[0], addr[1])
                )
                self.cmd_channel.log(msg, logfun=logger.warning)

        self.close()

        if self.cmd_channel.connected:
            handler = self.cmd_channel.dtp_handler(sock, self.cmd_channel)
            if handler.connected:
                self.cmd_channel.data_channel = handler
                self.cmd_channel._on_dtp_connection()

    def handle_timeout(self):
        if self.cmd_channel.connected:
            self.cmd_channel.respond(
                "421 Passive data channel timed out.", logfun=logger.info
            )
        self.close()

    def handle_error(self):
        "a"
        try:
            raise
        except Exception:
            logger.error(traceback.format_exc())
        try:
            self.close()
        except Exception:
            logger.critical(traceback.format_exc())

    def close(self):
        debug("call: close()", inst=self)
        Acceptor.close(self)


class ActiveDTP(Connector):
    "a"

    timeout = 30

    def __init__(self, ip, port, cmd_channel):
        "a"
        Connector.__init__(self, ioloop=cmd_channel.ioloop)
        self.cmd_channel = cmd_channel
        self.log = cmd_channel.log
        self.log_exception = cmd_channel.log_exception
        self._idler = None
        if self.timeout:
            self._idler = self.ioloop.call_later(
                self.timeout, self.handle_timeout, _errback=self.handle_error
            )

        if ip.count('.') == 3:
            self._cmd = "PORT"
            self._normalized_addr = "%s:%s" % (ip, port)
        else:
            self._cmd = "EPRT"
            self._normalized_addr = "[%s]:%s" % (ip, port)

        source_ip = self.cmd_channel.socket.getsockname()[0]

        try:
            self.connect_af_unspecified((ip, port), (source_ip, 0))
        except (socket.gaierror, socket.error):
            self.handle_close()

    def readable(self):
        return False

    def handle_connect(self):
        "a"
        self.del_channel()
        if self._idler is not None and not self._idler.cancelled:
            self._idler.cancel()
        if not self.cmd_channel.connected:
            return self.close()

        err = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if err != 0:
            raise socket.error(err)

        msg = 'Active data connection established.'
        self.cmd_channel.respond('200 ' + msg)
        self.cmd_channel.log_cmd(self._cmd, self._normalized_addr, 200, msg)

        if not self.cmd_channel.connected:
            return self.close()

        handler = self.cmd_channel.dtp_handler(self.socket, self.cmd_channel)
        self.cmd_channel.data_channel = handler
        self.cmd_channel._on_dtp_connection()

    def handle_timeout(self):
        if self.cmd_channel.connected:
            msg = "Active data channel timed out."
            self.cmd_channel.respond("421 " + msg, logfun=logger.info)
            self.cmd_channel.log_cmd(
                self._cmd, self._normalized_addr, 421, msg
            )
        self.close()

    def handle_close(self):

        if not self._closed:
            self.close()
            if self.cmd_channel.connected:
                msg = "Can't connect to specified address."
                self.cmd_channel.respond("425 " + msg)
                self.cmd_channel.log_cmd(
                    self._cmd, self._normalized_addr, 425, msg
                )

    def handle_error(self):
        "a"
        try:
            raise
        except (socket.gaierror, socket.error):
            pass
        except Exception:
            self.log_exception(self)
        try:
            self.handle_close()
        except Exception:
            logger.critical(traceback.format_exc())

    def close(self):
        debug("call: close()", inst=self)
        if not self._closed:
            Connector.close(self)
            if self._idler is not None and not self._idler.cancelled:
                self._idler.cancel()


class DTPHandler(AsyncChat):
    "a"

    timeout = 300
    ac_in_buffer_size = 65536
    ac_out_buffer_size = 65536

    def __init__(self, sock, cmd_channel):
        "a"
        self.cmd_channel = cmd_channel
        self.file_obj = None
        self.receive = False
        self.transfer_finished = False
        self.tot_bytes_sent = 0
        self.tot_bytes_received = 0
        self.cmd = None
        self.log = cmd_channel.log
        self.log_exception = cmd_channel.log_exception
        self._data_wrapper = None
        self._lastdata = 0
        self._had_cr = False
        self._start_time = timer()
        self._resp = ()
        self._offset = None
        self._filefd = None
        self._idler = None
        self._initialized = False
        try:
            AsyncChat.__init__(self, sock, ioloop=cmd_channel.ioloop)
        except socket.error as err:

            AsyncChat.__init__(
                self, socket.socket(), ioloop=cmd_channel.ioloop
            )

            self.close()
            if err.errno == errno.EINVAL:
                return
            self.handle_error()
            return

        if not self.connected:
            self.close()
            return
        if self.timeout:
            self._idler = self.ioloop.call_every(
                self.timeout, self.handle_timeout, _errback=self.handle_error
            )

    def __repr__(self):
        return '<%s(%s)>' % (
            self.__class__.__name__,
            self.cmd_channel.get_repr_info(as_str=True),
        )

    __str__ = __repr__

    def use_sendfile(self):
        if not self.cmd_channel.use_sendfile:

            return False
        if self.file_obj is None or not hasattr(self.file_obj, "fileno"):

            return False
        try:

            self.file_obj.fileno()
        except (OSError, ValueError):
            return False
        if self.cmd_channel._current_type != 'i':

            return False
        return True

    def push(self, data):
        self._initialized = True
        self.modify_ioloop_events(self.ioloop.WRITE)
        self._wanted_io_events = self.ioloop.WRITE
        AsyncChat.push(self, data)

    def push_with_producer(self, producer):
        self._initialized = True
        self.modify_ioloop_events(self.ioloop.WRITE)
        self._wanted_io_events = self.ioloop.WRITE
        if self.use_sendfile():
            self._offset = producer.file.tell()
            self._filefd = self.file_obj.fileno()
            try:
                self.initiate_sendfile()
            except _GiveUpOnSendfile:
                pass
            else:
                self.initiate_send = self.initiate_sendfile
                return
        debug("starting transfer using send()", self)
        AsyncChat.push_with_producer(self, producer)

    def close_when_done(self):
        asynchat.async_chat.close_when_done(self)

    def initiate_send(self):
        asynchat.async_chat.initiate_send(self)

    def initiate_sendfile(self):
        "a"
        try:
            sent = sendfile(
                self._fileno,
                self._filefd,
                self._offset,
                self.ac_out_buffer_size,
            )
        except OSError as err:
            if err.errno in _ERRNOS_RETRY or err.errno == errno.EBUSY:
                return
            elif err.errno in _ERRNOS_DISCONNECTED:
                self.handle_close()
            else:
                if self.tot_bytes_sent == 0:
                    logger.warning(
                        "sendfile() failed; falling back on using plain send"
                    )
                    raise _GiveUpOnSendfile
                else:
                    raise
        else:
            if sent == 0:

                self.discard_buffers()
                self.handle_close()
            else:
                self._offset += sent
                self.tot_bytes_sent += sent


    def _posix_ascii_data_wrapper(self, chunk):
        "a"
        if self._had_cr:
            chunk = b'\r' + chunk

        if chunk.endswith(b'\r'):
            self._had_cr = True
            chunk = chunk[:-1]
        else:
            self._had_cr = False

        return chunk.replace(b'\r\n', b(os.linesep))

    def enable_receiving(self, type, cmd):
        "a"
        self._initialized = True
        self.modify_ioloop_events(self.ioloop.READ)
        self._wanted_io_events = self.ioloop.READ
        self.cmd = cmd
        if type == 'a':
            if os.linesep == '\r\n':
                self._data_wrapper = None
            else:
                self._data_wrapper = self._posix_ascii_data_wrapper
        elif type == 'i':
            self._data_wrapper = None
        else:
            raise TypeError("unsupported type")
        self.receive = True

    def get_transmitted_bytes(self):
        "a"
        return self.tot_bytes_sent + self.tot_bytes_received

    def get_elapsed_time(self):
        "a"
        return timer() - self._start_time

    def transfer_in_progress(self):
        "a"
        return self.get_transmitted_bytes() != 0


    def send(self, data):
        result = AsyncChat.send(self, data)
        self.tot_bytes_sent += result
        return result

    def refill_buffer(self):
        "a"
        while True:
            if len(self.producer_fifo):
                p = self.producer_fifo.first()

                if p is None:
                    if not self.ac_out_buffer:
                        self.producer_fifo.pop()

                        self.handle_close()
                    return
                elif isinstance(p, str):
                    self.producer_fifo.pop()
                    self.ac_out_buffer += p
                    return
                data = p.more()
                if data:
                    self.ac_out_buffer = self.ac_out_buffer + data
                    return
                else:
                    self.producer_fifo.pop()
            else:
                return

    def handle_read(self):
        "a"
        try:
            chunk = self.recv(self.ac_in_buffer_size)
        except RetryError:
            pass
        except socket.error:
            self.handle_error()
        else:
            self.tot_bytes_received += len(chunk)
            if not chunk:
                self.transfer_finished = True

                return
            if self._data_wrapper is not None:
                chunk = self._data_wrapper(chunk)
            try:
                self.file_obj.write(chunk)
            except OSError as err:
                raise _FileReadWriteError(err)

    handle_read_event = handle_read

    def readable(self):
        "a"

        if not self.receive and not self._initialized:
            return self.close()
        return self.receive

    def writable(self):
        "a"
        return not self.receive and asynchat.async_chat.writable(self)

    def handle_timeout(self):
        "a"
        if self.get_transmitted_bytes() > self._lastdata:
            self._lastdata = self.get_transmitted_bytes()
        else:
            msg = "Data connection timed out."
            self._resp = ("421 " + msg, logger.info)
            self.close()
            self.cmd_channel.close_when_done()

    def handle_error(self):
        "a"
        try:
            raise

        except _FileReadWriteError as err:
            error = _strerror(err.errno)
        except Exception:

            self.log_exception(self)
            error = "Internal error"
        try:
            self._resp = ("426 %s; transfer aborted." % error, logger.warning)
            self.close()
        except Exception:
            logger.critical(traceback.format_exc())

    def handle_close(self):
        "a"

        if not self._closed:
            if self.receive:
                self.transfer_finished = True
            else:
                self.transfer_finished = len(self.producer_fifo) == 0
            try:
                if self.transfer_finished:
                    self._resp = ("226 Transfer complete.", logger.debug)
                else:
                    tot_bytes = self.get_transmitted_bytes()
                    self._resp = (
                        "426 Transfer aborted; %d bytes transmitted."
                        % tot_bytes,
                        logger.debug,
                    )
            finally:
                self.close()

    def close(self):
        "a"
        debug("call: close()", inst=self)
        if not self._closed:

            AsyncChat.close(self)

            if self.file_obj is not None and not self.file_obj.closed:
                self.file_obj.close()

            if self._resp:
                self.cmd_channel.respond(self._resp[0], logfun=self._resp[1])

            if self._idler is not None and not self._idler.cancelled:
                self._idler.cancel()
            if self.file_obj is not None:
                filename = self.file_obj.name
                elapsed_time = round(self.get_elapsed_time(), 3)
                self.cmd_channel.log_transfer(
                    cmd=self.cmd,
                    filename=self.file_obj.name,
                    receive=self.receive,
                    completed=self.transfer_finished,
                    elapsed=elapsed_time,
                    bytes=self.get_transmitted_bytes(),
                )
                if self.transfer_finished:
                    if self.receive:
                        self.cmd_channel.on_file_received(filename)
                    else:
                        self.cmd_channel.on_file_sent(filename)
                else:
                    if self.receive:
                        self.cmd_channel.on_incomplete_file_received(filename)
                    else:
                        self.cmd_channel.on_incomplete_file_sent(filename)
            self.cmd_channel._on_dtp_close()

if PY3:

    class _AsyncChatNewStyle(AsyncChat):
        pass

else:

    class _AsyncChatNewStyle(object, AsyncChat):

        def __init__(self, *args, **kwargs):
            super(object, self).__init__(*args, **kwargs)


class ThrottledDTPHandler(_AsyncChatNewStyle, DTPHandler):
    "a"

    read_limit = 0
    write_limit = 0
    auto_sized_buffers = True

    def __init__(self, sock, cmd_channel):
        super().__init__(sock, cmd_channel)
        self._timenext = 0
        self._datacount = 0
        self.sleeping = False
        self._throttler = None
        if self.auto_sized_buffers:
            if self.read_limit:
                while self.ac_in_buffer_size > self.read_limit:
                    self.ac_in_buffer_size /= 2
            if self.write_limit:
                while self.ac_out_buffer_size > self.write_limit:
                    self.ac_out_buffer_size /= 2
        self.ac_in_buffer_size = int(self.ac_in_buffer_size)
        self.ac_out_buffer_size = int(self.ac_out_buffer_size)

    def __repr__(self):
        return DTPHandler.__repr__(self)

    def use_sendfile(self):
        return False

    def recv(self, buffer_size):
        chunk = super().recv(buffer_size)
        if self.read_limit:
            self._throttle_bandwidth(len(chunk), self.read_limit)
        return chunk

    def send(self, data):
        num_sent = super().send(data)
        if self.write_limit:
            self._throttle_bandwidth(num_sent, self.write_limit)
        return num_sent

    def _cancel_throttler(self):
        if self._throttler is not None and not self._throttler.cancelled:
            self._throttler.cancel()

    def _throttle_bandwidth(self, len_chunk, max_speed):
        "a"
        self._datacount += len_chunk
        if self._datacount >= max_speed:
            self._datacount = 0
            now = timer()
            sleepfor = (self._timenext - now) * 2
            if sleepfor > 0:

                def unsleep():
                    if self.receive:
                        event = self.ioloop.READ
                    else:
                        event = self.ioloop.WRITE
                    self.add_channel(events=event)

                self.del_channel()
                self._cancel_throttler()
                self._throttler = self.ioloop.call_later(
                    sleepfor, unsleep, _errback=self.handle_error
                )
            self._timenext = now + 1

    def close(self):
        self._cancel_throttler()
        super().close()



class FileProducer(object):
    "a"

    buffer_size = 65536

    def __init__(self, file, type):
        "a"
        self.file = file
        self.type = type
        self._prev_chunk_endswith_cr = False
        if type == 'a' and os.linesep != '\r\n':
            self._data_wrapper = self._posix_ascii_data_wrapper
        else:
            self._data_wrapper = None

    def _posix_ascii_data_wrapper(self, chunk):
        "a"
        chunk = bytearray(chunk)
        pos = 0
        if self._prev_chunk_endswith_cr and chunk.startswith(b'\n'):
            pos += 1
        while True:
            pos = chunk.find(b'\n', pos)
            if pos == -1:
                break
            if chunk[pos - 1] != CR_BYTE:
                chunk.insert(pos, CR_BYTE)
                pos += 1
            pos += 1
        self._prev_chunk_endswith_cr = chunk.endswith(b'\r')
        return chunk

    def more(self):
        "a"
        try:
            data = self.file.read(self.buffer_size)
        except OSError as err:
            raise _FileReadWriteError(err)
        else:
            if self._data_wrapper is not None:
                data = self._data_wrapper(data)
            return data


class BufferedIteratorProducer(object):
    "a"

    loops = 20

    def __init__(self, iterator):
        self.iterator = iterator

    def more(self):
        "a"
        buffer = []
        for _ in xrange(self.loops):
            try:
                buffer.append(next(self.iterator))
            except StopIteration:
                break
        return b''.join(buffer)



class FTPHandler(AsyncChat):
    "a"

    authorizer = DummyAuthorizer()
    active_dtp = ActiveDTP
    passive_dtp = PassiveDTP
    dtp_handler = DTPHandler
    abstracted_fs = AbstractedFS
    proto_cmds = proto_cmds

    timeout = 300
    banner = "pyftpdlib %s ready." % __ver__
    max_login_attempts = 3
    permit_foreign_addresses = False
    permit_privileged_ports = False
    masquerade_address = None
    masquerade_address_map = {}
    passive_ports = None
    use_gmt_times = True
    use_sendfile = sendfile is not None
    tcp_no_delay = hasattr(socket, "TCP_NODELAY")
    unicode_errors = 'replace'
    log_prefix = '%(remote_ip)s:%(remote_port)s-[%(username)s]'
    auth_failed_timeout = 3

    def __init__(self, conn, server, ioloop=None):
        "a"

        self.server = server
        self.fs = None
        self.authenticated = False
        self.username = ""
        self.password = ""
        self.attempted_logins = 0
        self.data_channel = None
        self.remote_ip = ""
        self.remote_port = ""
        self.started = time.time()

        self._last_response = ""
        self._current_type = 'a'
        self._restart_position = 0
        self._quit_pending = False
        self._in_buffer = []
        self._in_buffer_len = 0
        self._epsvall = False
        self._dtp_acceptor = None
        self._dtp_connector = None
        self._in_dtp_queue = None
        self._out_dtp_queue = None
        self._extra_feats = []
        self._current_facts = ['type', 'perm', 'size', 'modify']
        self._rnfr = None
        self._idler = None
        self._log_debug = (
            logging.getLogger('pyftpdlib').getEffectiveLevel() <= logging.DEBUG
        )

        if os.name == 'posix':
            self._current_facts.append('unique')
        self._available_facts = self._current_facts[:]
        if pwd and grp:
            self._available_facts += ['unix.mode', 'unix.uid', 'unix.gid']
        if os.name == 'nt':
            self._available_facts.append('create')

        try:
            AsyncChat.__init__(self, conn, ioloop=ioloop)
        except socket.error as err:

            AsyncChat.__init__(self, socket.socket(), ioloop=ioloop)
            self.close()
            debug("call: FTPHandler.__init__, err %r" % err, self)
            if err.errno == errno.EINVAL:

                return
            self.handle_error()
            return
        self.set_terminator(b"\r\n")

        try:
            self.remote_ip, self.remote_port = self.socket.getpeername()[:2]
        except socket.error as err:
            debug(
                "call: FTPHandler.__init__, err on getpeername() %r" % err,
                self,
            )

            self.connected = False
            if err.errno in (errno.ENOTCONN, errno.EINVAL):
                self.close()
            else:
                self.handle_error()
            return
        else:
            self.log("FTP session opened (connect)")

        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_OOBINLINE, 1)
        except socket.error as err:
            debug(
                "call: FTPHandler.__init__, err on SO_OOBINLINE %r" % err, self
            )

        if self.tcp_no_delay:
            try:
                self.socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
            except socket.error as err:
                debug(
                    "call: FTPHandler.__init__, err on TCP_NODELAY %r" % err,
                    self,
                )

        if not self.connected:
            self.close()
            return

        if self.timeout:
            self._idler = self.ioloop.call_later(
                self.timeout, self.handle_timeout, _errback=self.handle_error
            )

    def get_repr_info(self, as_str=False, extra_info=None):
        if extra_info is None:
            extra_info = {}
        info = OrderedDict()
        info['id'] = id(self)
        info['addr'] = "%s:%s" % (self.remote_ip, self.remote_port)
        if _is_ssl_sock(self.socket):
            info['ssl'] = True
        if self.username:
            info['user'] = self.username

        dc = getattr(self, 'data_channel', None)
        if dc is not None:
            if _is_ssl_sock(dc.socket):
                info['ssl-data'] = True
            if dc.file_obj:
                if self.data_channel.receive:
                    info['sending-file'] = dc.file_obj
                    if dc.use_sendfile():
                        info['use-sendfile(2)'] = True
                else:
                    info['receiving-file'] = dc.file_obj
                info['bytes-trans'] = dc.get_transmitted_bytes()
        info.update(extra_info)
        if as_str:
            return ', '.join(['%s=%r' % (k, v) for (k, v) in info.items()])
        return info

    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, self.get_repr_info(True))

    __str__ = __repr__

    def handle(self):
        "a"
        self.on_connect()
        if not self._closed and not self._closing:
            if len(self.banner) <= 75:
                self.respond("220 %s" % str(self.banner))
            else:
                self.push('220-%s\r\n' % str(self.banner))
                self.respond('220 ')

    def handle_max_cons(self):
        "a"
        msg = "421 Too many connections. Service temporarily unavailable."
        self.respond_w_warning(msg)

        self.close()

    def handle_max_cons_per_ip(self):
        "a"
        msg = "421 Too many connections from the same IP address."
        self.respond_w_warning(msg)
        self.close_when_done()

    def handle_timeout(self):
        "a"
        msg = "Control connection timed out."
        self.respond("421 " + msg, logfun=logger.info)
        self.close_when_done()


    def readable(self):

        return self.connected and AsyncChat.readable(self)

    def writable(self):
        return self.connected and AsyncChat.writable(self)

    def collect_incoming_data(self, data):
        "a"
        self._in_buffer.append(data)
        self._in_buffer_len += len(data)

        buflimit = 2048
        if self._in_buffer_len > buflimit:
            self.respond_w_warning('500 Command too long.')
            self._in_buffer = []
            self._in_buffer_len = 0

    def decode(self, bytes):
        return bytes.decode('utf8', self.unicode_errors)

    def found_terminator(self):
        "a"
        if self._idler is not None and not self._idler.cancelled:
            self._idler.reset()

        line = b''.join(self._in_buffer)
        try:
            line = self.decode(line)
        except UnicodeDecodeError:

            return self.respond("501 Can't decode command.")

        self._in_buffer = []
        self._in_buffer_len = 0

        cmd = line.split(' ')[0].upper()
        arg = line[len(cmd) + 1 :]
        try:
            self.pre_process_command(line, cmd, arg)
        except UnicodeEncodeError:
            self.respond(
                "501 can't decode path (server filesystem encoding is %s)"
                % sys.getfilesystemencoding()
            )

    def pre_process_command(self, line, cmd, arg):
        kwargs = {}
        if cmd == "SITE" and arg:
            cmd = "SITE %s" % arg.split(' ')[0].upper()
            arg = line[len(cmd) + 1 :]

        if cmd != 'PASS':
            self.logline("<- %s" % line)
        else:
            self.logline("<- %s %s" % (line.split(' ')[0], '*' * 6))

        if cmd not in self.proto_cmds:
            if cmd[-4:] in ('ABOR', 'STAT', 'QUIT'):
                cmd = cmd[-4:]
            else:
                msg = 'Command "%s" not understood.' % cmd
                self.respond('500 ' + msg)
                if cmd:
                    self.log_cmd(cmd, arg, 500, msg)
                return

        if not arg and self.proto_cmds[cmd]['arg'] is True:
            msg = "Syntax error: command needs an argument."
            self.respond("501 " + msg)
            self.log_cmd(cmd, "", 501, msg)
            return
        if arg and self.proto_cmds[cmd]['arg'] is False:
            msg = "Syntax error: command does not accept arguments."
            self.respond("501 " + msg)
            self.log_cmd(cmd, arg, 501, msg)
            return

        if not self.authenticated:
            if self.proto_cmds[cmd]['auth'] or (cmd == 'STAT' and arg):
                msg = "Log in with USER and PASS first."
                self.respond("530 " + msg)
                self.log_cmd(cmd, arg, 530, msg)
            else:

                self.process_command(cmd, arg)
                return
        else:
            if (cmd == 'STAT') and not arg:
                self.ftp_STAT(u(''))
                return

            if self.proto_cmds[cmd]['perm'] and (cmd != 'STOU'):
                if cmd in ('CWD', 'XCWD'):
                    arg = self.fs.ftp2fs(arg or u('/'))
                elif cmd in ('CDUP', 'XCUP'):
                    arg = self.fs.ftp2fs(u('..'))
                elif cmd == 'LIST':
                    if arg.lower() in ('-a', '-l', '-al', '-la'):
                        arg = self.fs.ftp2fs(self.fs.cwd)
                    else:
                        arg = self.fs.ftp2fs(arg or self.fs.cwd)
                elif cmd == 'STAT':
                    if glob.has_magic(arg):
                        msg = 'Globbing not supported.'
                        self.respond('550 ' + msg)
                        self.log_cmd(cmd, arg, 550, msg)
                        return
                    arg = self.fs.ftp2fs(arg or self.fs.cwd)
                elif cmd == 'SITE CHMOD':
                    if ' ' not in arg:
                        msg = "Syntax error: command needs two arguments."
                        self.respond("501 " + msg)
                        self.log_cmd(cmd, "", 501, msg)
                        return
                    else:
                        mode, arg = arg.split(' ', 1)
                        arg = self.fs.ftp2fs(arg)
                        kwargs = dict(mode=mode)
                elif cmd == 'MFMT':
                    if ' ' not in arg:
                        msg = "Syntax error: command needs two arguments."
                        self.respond("501 " + msg)
                        self.log_cmd(cmd, "", 501, msg)
                        return
                    else:
                        timeval, arg = arg.split(' ', 1)
                        arg = self.fs.ftp2fs(arg)
                        kwargs = dict(timeval=timeval)

                else:
                    arg = self.fs.ftp2fs(arg or self.fs.cwd)

                if not self.fs.validpath(arg):
                    line = self.fs.fs2ftp(arg)
                    msg = "%r points to a path which is outside " % line
                    msg += "the user's root directory"
                    self.respond("550 %s." % msg)
                    self.log_cmd(cmd, arg, 550, msg)
                    return

            perm = self.proto_cmds[cmd]['perm']
            if perm is not None and cmd != 'STOU':
                if not self.authorizer.has_perm(self.username, perm, arg):
                    msg = "Not enough privileges."
                    self.respond("550 " + msg)
                    self.log_cmd(cmd, arg, 550, msg)
                    return

            self.process_command(cmd, arg, **kwargs)

    def process_command(self, cmd, *args, **kwargs):
        "a"
        if self._closed:
            return
        self._last_response = ""
        method = getattr(self, 'ftp_' + cmd.replace(' ', '_'))
        method(*args, **kwargs)
        if self._last_response:
            code = int(self._last_response[:3])
            resp = self._last_response[4:]
            self.log_cmd(cmd, args[0], code, resp)

    def handle_error(self):
        try:
            self.log_exception(self)
            self.close()
        except Exception:
            logger.critical(traceback.format_exc())

    def handle_close(self):
        self.close()

    def close(self):
        "a"
        debug("call: close()", inst=self)
        if not self._closed:
            AsyncChat.close(self)

            self._shutdown_connecting_dtp()

            if self.data_channel is not None:
                self.data_channel.close()
                del self.data_channel

            if self._out_dtp_queue is not None:
                file = self._out_dtp_queue[2]
                if file is not None:
                    file.close()
            if self._in_dtp_queue is not None:
                file = self._in_dtp_queue[0]
                if file is not None:
                    file.close()

            del self._out_dtp_queue
            del self._in_dtp_queue

            if self._idler is not None and not self._idler.cancelled:
                self._idler.cancel()

            if self.remote_ip in self.server.ip_map:
                self.server.ip_map.remove(self.remote_ip)

            if self.fs is not None:
                self.fs.cmd_channel = None
                self.fs = None
            self.log("FTP session closed (disconnect).")

            if self.remote_ip:
                self.ioloop.call_later(
                    0, self.on_disconnect, _errback=self.handle_error
                )

    def _shutdown_connecting_dtp(self):
        "a"
        if self._dtp_acceptor is not None:
            self._dtp_acceptor.close()
            self._dtp_acceptor = None
        if self._dtp_connector is not None:
            self._dtp_connector.close()
            self._dtp_connector = None


    def on_connect(self):
        "a"

    def on_disconnect(self):
        "a"

    def on_login(self, username):
        "a"

    def on_login_failed(self, username, password):
        "a"

    def on_logout(self, username):
        "a"

    def on_file_sent(self, file):
        "a"

    def on_file_received(self, file):
        "a"

    def on_incomplete_file_sent(self, file):
        "a"

    def on_incomplete_file_received(self, file):
        "a"


    def _on_dtp_connection(self):
        "a"

        if self._dtp_acceptor is not None:
            self._dtp_acceptor.close()
            self._dtp_acceptor = None

        if self._idler is not None and not self._idler.cancelled:
            self._idler.cancel()

        if self._out_dtp_queue is not None:
            data, isproducer, file, cmd = self._out_dtp_queue
            self._out_dtp_queue = None
            self.data_channel.cmd = cmd
            if file:
                self.data_channel.file_obj = file
            try:
                if not isproducer:
                    self.data_channel.push(data)
                else:
                    self.data_channel.push_with_producer(data)
                if self.data_channel is not None:
                    self.data_channel.close_when_done()
            except Exception:

                self.data_channel.handle_error()

        elif self._in_dtp_queue is not None:
            file, cmd = self._in_dtp_queue
            self.data_channel.file_obj = file
            self._in_dtp_queue = None
            self.data_channel.enable_receiving(self._current_type, cmd)

    def _on_dtp_close(self):
        "a"
        self.data_channel = None
        if self._quit_pending:
            self.close()
        elif self.timeout:

            if self._idler is not None and not self._idler.cancelled:
                self._idler.cancel()
            self._idler = self.ioloop.call_later(
                self.timeout, self.handle_timeout, _errback=self.handle_error
            )


    def push(self, data):
        asynchat.async_chat.push(self, data.encode('utf8'))

    def respond(self, resp, logfun=logger.debug):
        "a"
        self._last_response = resp
        self.push(resp + '\r\n')
        if self._log_debug:
            self.logline('-> %s' % resp, logfun=logfun)
        else:
            self.log(resp[4:], logfun=logfun)

    def respond_w_warning(self, resp):
        self.respond(resp, logfun=logger.warning)

    def push_dtp_data(self, data, isproducer=False, file=None, cmd=None):
        "a"
        if self.data_channel is not None:
            self.respond(
                "125 Data connection already open. Transfer starting."
            )
            if file:
                self.data_channel.file_obj = file
            try:
                if not isproducer:
                    self.data_channel.push(data)
                else:
                    self.data_channel.push_with_producer(data)
                if self.data_channel is not None:
                    self.data_channel.cmd = cmd
                    self.data_channel.close_when_done()
            except Exception:

                self.data_channel.handle_error()
        else:
            self.respond(
                "150 File status okay. About to open data connection."
            )
            self._out_dtp_queue = (data, isproducer, file, cmd)

    def flush_account(self):
        "a"
        self._shutdown_connecting_dtp()

        if self.data_channel is not None:
            if not self.data_channel.transfer_in_progress():
                self.data_channel.close()
                self.data_channel = None

        username = self.username
        if self.authenticated and username:
            self.on_logout(username)
        self.authenticated = False
        self.username = ""
        self.password = ""
        self.attempted_logins = 0
        self._current_type = 'a'
        self._restart_position = 0
        self._quit_pending = False
        self._in_dtp_queue = None
        self._rnfr = None
        self._out_dtp_queue = None

    def run_as_current_user(self, function, *args, **kwargs):
        "a"
        self.authorizer.impersonate_user(self.username, self.password)
        try:
            return function(*args, **kwargs)
        finally:
            self.authorizer.terminate_impersonation(self.username)


    def log(self, msg, logfun=logger.info):
        "a"
        prefix = self.log_prefix % self.__dict__
        logfun("%s %s" % (prefix, msg))

    def logline(self, msg, logfun=logger.debug):
        "a"
        if self._log_debug:
            prefix = self.log_prefix % self.__dict__
            logfun("%s %s" % (prefix, msg))

    def logerror(self, msg):
        "a"
        prefix = self.log_prefix % self.__dict__
        logger.error("%s %s" % (prefix, msg))

    def log_exception(self, instance):
        "a"
        logger.exception("unhandled exception in instance %r", instance)

    log_cmds_list = [
        "DELE",
        "RNFR",
        "RNTO",
        "MKD",
        "RMD",
        "CWD",
        "XMKD",
        "XRMD",
        "XCWD",
        "REIN",
        "SITE CHMOD",
        "MFMT",
    ]

    def log_cmd(self, cmd, arg, respcode, respstr):
        "a"
        if not self._log_debug and cmd in self.log_cmds_list:
            line = '%s %s' % (' '.join([cmd, arg]).strip(), respcode)
            if str(respcode)[0] in ('4', '5'):
                line += ' %r' % respstr
            self.log(line)

    def log_transfer(self, cmd, filename, receive, completed, elapsed, bytes):
        "a"
        line = '%s %s completed=%s bytes=%s seconds=%s' % (
            cmd,
            filename,
            completed and 1 or 0,
            bytes,
            elapsed,
        )
        self.log(line)

    def _make_eport(self, ip, port):
        "a"

        remote_ip = self.remote_ip
        if remote_ip.startswith('::ffff:'):

            remote_ip = remote_ip[7:]
        if not self.permit_foreign_addresses and ip != remote_ip:
            msg = "501 Rejected data connection to foreign address %s:%s." % (
                ip,
                port,
            )
            self.respond_w_warning(msg)
            return

        if not self.permit_privileged_ports and port < 1024:
            msg = '501 PORT against the privileged port "%s" refused.' % port
            self.respond_w_warning(msg)
            return

        self._shutdown_connecting_dtp()

        if self.data_channel is not None:
            self.data_channel.close()
            self.data_channel = None

        if not self.server._accept_new_cons():
            msg = "425 Too many connections. Can't open data channel."
            self.respond_w_warning(msg)
            return

        self._dtp_connector = self.active_dtp(ip, port, self)

    def _make_epasv(self, extmode=False):
        "a"

        self._shutdown_connecting_dtp()

        if self.data_channel is not None:
            self.data_channel.close()
            self.data_channel = None

        if not self.server._accept_new_cons():
            msg = "425 Too many connections. Can't open data channel."
            self.respond_w_warning(msg)
            return

        self._dtp_acceptor = self.passive_dtp(self, extmode)

    def ftp_PORT(self, line):
        "a"
        if self._epsvall:
            self.respond("501 PORT not allowed after EPSV ALL.")
            return

        try:
            addr = list(map(int, line.split(',')))
            if len(addr) != 6:
                raise ValueError
            for x in addr[:4]:
                if not 0 <= x <= 255:
                    raise ValueError
            ip = '%d.%d.%d.%d' % tuple(addr[:4])
            port = (addr[4] * 256) + addr[5]
            if not 0 <= port <= 65535:
                raise ValueError
        except (ValueError, OverflowError):
            self.respond("501 Invalid PORT format.")
            return
        self._make_eport(ip, port)

    def ftp_EPRT(self, line):
        "a"
        if self._epsvall:
            self.respond("501 EPRT not allowed after EPSV ALL.")
            return

        try:
            af, ip, port = line.split(line[0])[1:-1]
            port = int(port)
            if not 0 <= port <= 65535:
                raise ValueError
        except (ValueError, IndexError, OverflowError):
            self.respond("501 Invalid EPRT format.")
            return

        if af == "1":

            if (
                self.socket.family == socket.AF_INET6
                and not SUPPORTS_HYBRID_IPV6
            ):
                self.respond('522 Network protocol not supported (use 2).')
            else:
                try:
                    octs = list(map(int, ip.split('.')))
                    if len(octs) != 4:
                        raise ValueError
                    for x in octs:
                        if not 0 <= x <= 255:
                            raise ValueError
                except (ValueError, OverflowError):
                    self.respond("501 Invalid EPRT format.")
                else:
                    self._make_eport(ip, port)
        elif af == "2":
            if self.socket.family == socket.AF_INET:
                self.respond('522 Network protocol not supported (use 1).')
            else:
                self._make_eport(ip, port)
        else:
            if self.socket.family == socket.AF_INET:
                self.respond('501 Unknown network protocol (use 1).')
            else:
                self.respond('501 Unknown network protocol (use 2).')

    def ftp_PASV(self, line):
        "a"
        if self._epsvall:
            self.respond("501 PASV not allowed after EPSV ALL.")
            return
        self._make_epasv(extmode=False)

    def ftp_EPSV(self, line):
        "a"

        if not line:
            self._make_epasv(extmode=True)

        elif line == "1":
            if self.socket.family != socket.AF_INET:
                self.respond('522 Network protocol not supported (use 2).')
            else:
                self._make_epasv(extmode=True)

        elif line == "2":
            if self.socket.family == socket.AF_INET:
                self.respond('522 Network protocol not supported (use 1).')
            else:
                self._make_epasv(extmode=True)
        elif line.lower() == 'all':
            self._epsvall = True
            self.respond(
                '220 Other commands other than EPSV are now disabled.'
            )
        else:
            if self.socket.family == socket.AF_INET:
                self.respond('501 Unknown network protocol (use 1).')
            else:
                self.respond('501 Unknown network protocol (use 2).')

    def ftp_QUIT(self, line):
        "a"
        if self.authenticated:
            msg_quit = self.authorizer.get_msg_quit(self.username)
        else:
            msg_quit = "Goodbye."
        if len(msg_quit) <= 75:
            self.respond("221 %s" % msg_quit)
        else:
            self.push("221-%s\r\n" % msg_quit)
            self.respond("221 ")

        if self.data_channel:
            self._quit_pending = True
            self.del_channel()
        else:
            self._shutdown_connecting_dtp()
            self.close_when_done()
        if self.authenticated and self.username:
            self.on_logout(self.username)


    def ftp_LIST(self, path):
        "a"

        try:
            isdir = self.fs.isdir(path)
            if isdir:
                listing = self.run_as_current_user(self.fs.listdir, path)
                if isinstance(listing, list):
                    try:

                        listing.sort()
                    except UnicodeDecodeError:

                        pass
                iterator = self.fs.format_list(path, listing)
            else:
                basedir, filename = os.path.split(path)
                self.fs.lstat(path)
                iterator = self.fs.format_list(basedir, [filename])
        except (OSError, FilesystemError) as err:
            why = _strerror(err)
            self.respond('550 %s.' % why)
        else:
            producer = BufferedIteratorProducer(iterator)
            self.push_dtp_data(producer, isproducer=True, cmd="LIST")
            return path

    def ftp_NLST(self, path):
        "a"
        try:
            if self.fs.isdir(path):
                listing = list(self.run_as_current_user(self.fs.listdir, path))
            else:

                self.fs.lstat(path)
                listing = [os.path.basename(path)]
        except (OSError, FilesystemError) as err:
            self.respond('550 %s.' % _strerror(err))
        else:
            data = ''
            if listing:
                try:
                    listing.sort()
                except UnicodeDecodeError:

                    ls = []
                    for x in listing:
                        if not isinstance(x, unicode):
                            x = unicode(x, 'utf8')
                        ls.append(x)
                    listing = sorted(ls)
                data = '\r\n'.join(listing) + '\r\n'
            data = data.encode('utf8', self.unicode_errors)
            self.push_dtp_data(data, cmd="NLST")
            return path


    def ftp_MLST(self, path):
        "a"
        line = self.fs.fs2ftp(path)
        basedir, basename = os.path.split(path)
        perms = self.authorizer.get_perms(self.username)
        try:
            iterator = self.run_as_current_user(
                self.fs.format_mlsx,
                basedir,
                [basename],
                perms,
                self._current_facts,
                ignore_err=False,
            )
            data = b''.join(iterator)
        except (OSError, FilesystemError) as err:
            self.respond('550 %s.' % _strerror(err))
        else:
            data = data.decode('utf8', self.unicode_errors)

            data = data.split(' ')[0] + ' %s\r\n' % line

            self.push('250-Listing "%s":\r\n' % line)

            self.push(' ' + data)
            self.respond('250 End MLST.')
            return path

    def ftp_MLSD(self, path):
        "a"

        if not self.fs.isdir(path):
            self.respond("501 No such directory.")
            return
        try:
            listing = self.run_as_current_user(self.fs.listdir, path)
        except (OSError, FilesystemError) as err:
            why = _strerror(err)
            self.respond('550 %s.' % why)
        else:
            perms = self.authorizer.get_perms(self.username)
            iterator = self.fs.format_mlsx(
                path, listing, perms, self._current_facts
            )
            producer = BufferedIteratorProducer(iterator)
            self.push_dtp_data(producer, isproducer=True, cmd="MLSD")
            return path

    def ftp_RETR(self, file):
        "a"
        rest_pos = self._restart_position
        self._restart_position = 0
        try:
            fd = self.run_as_current_user(self.fs.open, file, 'rb')
        except (EnvironmentError, FilesystemError) as err:
            why = _strerror(err)
            self.respond('550 %s.' % why)
            return

        try:
            if rest_pos:

                ok = 0
                try:
                    fsize = self.fs.getsize(file)
                    if rest_pos > fsize:
                        raise ValueError
                    fd.seek(rest_pos)
                    ok = 1
                except ValueError:
                    why = "REST position (%s) > file size (%s)" % (
                        rest_pos,
                        fsize,
                    )
                except (EnvironmentError, FilesystemError) as err:
                    why = _strerror(err)
                if not ok:
                    fd.close()
                    self.respond('554 %s' % why)
                    return
            producer = FileProducer(fd, self._current_type)
            self.push_dtp_data(producer, isproducer=True, file=fd, cmd="RETR")
            return file
        except Exception:
            fd.close()
            raise

    def ftp_STOR(self, file, mode='w'):
        "a"

        cmd = 'APPE' if 'a' in mode else 'STOR'
        rest_pos = self._restart_position
        self._restart_position = 0
        if rest_pos:
            mode = 'r+'
        try:
            fd = self.run_as_current_user(self.fs.open, file, mode + 'b')
        except (EnvironmentError, FilesystemError) as err:
            why = _strerror(err)
            self.respond('550 %s.' % why)
            return

        try:
            if rest_pos:

                ok = 0
                try:
                    fsize = self.fs.getsize(file)
                    if rest_pos > fsize:
                        raise ValueError
                    fd.seek(rest_pos)
                    ok = 1
                except ValueError:
                    why = "REST position (%s) > file size (%s)" % (
                        rest_pos,
                        fsize,
                    )
                except (EnvironmentError, FilesystemError) as err:
                    why = _strerror(err)
                if not ok:
                    fd.close()
                    self.respond('554 %s' % why)
                    return

            if self.data_channel is not None:
                resp = "Data connection already open. Transfer starting."
                self.respond("125 " + resp)
                self.data_channel.file_obj = fd
                self.data_channel.enable_receiving(self._current_type, cmd)
            else:
                resp = "File status okay. About to open data connection."
                self.respond("150 " + resp)
                self._in_dtp_queue = (fd, cmd)
            return file
        except Exception:
            fd.close()
            raise

    def ftp_STOU(self, line):
        "a"

        if self._restart_position:
            self.respond("450 Can't STOU while REST request is pending.")
            return

        if line:
            basedir, prefix = os.path.split(self.fs.ftp2fs(line))
            prefix = prefix + '.'
        else:
            basedir = self.fs.ftp2fs(self.fs.cwd)
            prefix = 'ftpd.'
        try:
            fd = self.run_as_current_user(
                self.fs.mkstemp, prefix=prefix, dir=basedir
            )
        except (EnvironmentError, FilesystemError) as err:

            if getattr(err, "errno", -1) == errno.EEXIST:
                why = 'No usable unique file name found'

            else:
                why = _strerror(err)
            self.respond("450 %s." % why)
            return

        try:
            if not self.authorizer.has_perm(self.username, 'w', fd.name):
                try:
                    fd.close()
                    self.run_as_current_user(self.fs.remove, fd.name)
                except (OSError, FilesystemError):
                    pass
                self.respond("550 Not enough privileges.")
                return

            filename = os.path.basename(fd.name)
            if self.data_channel is not None:
                self.respond("125 FILE: %s" % filename)
                self.data_channel.file_obj = fd
                self.data_channel.enable_receiving(self._current_type, "STOU")
            else:
                self.respond("150 FILE: %s" % filename)
                self._in_dtp_queue = (fd, "STOU")
            return filename
        except Exception:
            fd.close()
            raise

    def ftp_APPE(self, file):
        "a"

        if self._restart_position:
            self.respond("450 Can't APPE while REST request is pending.")
        else:
            return self.ftp_STOR(file, mode='a')

    def ftp_REST(self, line):
        "a"
        if self._current_type == 'a':
            self.respond('501 Resuming transfers not allowed in ASCII mode.')
            return
        try:
            marker = int(line)
            if marker < 0:
                raise ValueError
        except (ValueError, OverflowError):
            self.respond("501 Invalid parameter.")
        else:
            self.respond("350 Restarting at position %s." % marker)
            self._restart_position = marker

    def ftp_ABOR(self, line):
        "a"

        if (
            self._dtp_acceptor is None
            and self._dtp_connector is None
            and self.data_channel is None
        ):
            self.respond("225 No transfer to abort.")
            return
        else:

            if (
                self._dtp_acceptor is not None
                or self._dtp_connector is not None
            ):
                self._shutdown_connecting_dtp()
                resp = "225 ABOR command successful; data channel closed."

            if self.data_channel is not None:
                if self.data_channel.transfer_in_progress():
                    self.data_channel.close()
                    self.data_channel = None
                    self.respond(
                        "426 Transfer aborted via ABOR.", logfun=logger.info
                    )
                    resp = "226 ABOR command successful."
                else:
                    self.data_channel.close()
                    self.data_channel = None
                    resp = "225 ABOR command successful; data channel closed."
        self.respond(resp)


    def ftp_USER(self, line):
        "a"

        if not self.authenticated:
            self.respond('331 Username ok, send password.')
        else:

            self.flush_account()
            msg = 'Previous account information was flushed'
            self.respond('331 %s, send password.' % msg, logfun=logger.info)
        self.username = line

    def handle_auth_failed(self, msg, password):
        def callback(username, password, msg):
            self.add_channel()
            if hasattr(self, '_closed') and not self._closed:
                self.attempted_logins += 1
                if self.attempted_logins >= self.max_login_attempts:
                    msg += " Disconnecting."
                    self.respond("530 " + msg)
                    self.close_when_done()
                else:
                    self.respond("530 " + msg)
                self.log("USER '%s' failed login." % username)
            self.on_login_failed(username, password)

        self.del_channel()
        if not msg:
            if self.username == 'anonymous':
                msg = "Anonymous access not allowed."
            else:
                msg = "Authentication failed."
        else:

            msg = msg.capitalize()
        self.ioloop.call_later(
            self.auth_failed_timeout,
            callback,
            self.username,
            password,
            msg,
            _errback=self.handle_error,
        )
        self.username = ""

    def handle_auth_success(self, home, password, msg_login):
        if not isinstance(home, unicode):
            if PY3:
                raise TypeError('type(home) != text')
            else:
                warnings.warn(
                    '%s.get_home_dir returned a non-unicode string; now '
                    'casting to unicode'
                    % (self.authorizer.__class__.__name__),
                    RuntimeWarning,
                    stacklevel=2,
                )
                home = home.decode('utf8')

        if len(msg_login) <= 75:
            self.respond('230 %s' % msg_login)
        else:
            self.push("230-%s\r\n" % msg_login)
            self.respond("230 ")
        self.log("USER '%s' logged in." % self.username)
        self.authenticated = True
        self.password = password
        self.attempted_logins = 0

        self.fs = self.abstracted_fs(home, self)
        self.on_login(self.username)

    def ftp_PASS(self, line):
        "a"
        if self.authenticated:
            self.respond("503 User already authenticated.")
            return
        if not self.username:
            self.respond("503 Login with USER first.")
            return

        try:
            self.authorizer.validate_authentication(self.username, line, self)
            home = self.authorizer.get_home_dir(self.username)
            msg_login = self.authorizer.get_msg_login(self.username)
        except (AuthenticationFailed, AuthorizerError) as err:
            self.handle_auth_failed(str(err), line)
        else:
            self.handle_auth_success(home, line, msg_login)

    def ftp_REIN(self, line):
        "a"

        self.flush_account()

        self.respond("230 Ready for new user.")


    def ftp_PWD(self, line):
        "a"

        cwd = self.fs.cwd
        assert isinstance(cwd, unicode), cwd
        self.respond(
            '257 "%s" is the current directory.' % cwd.replace('"', '""')
        )

    def ftp_CWD(self, path):
        "a"

        init_cwd = getcwdu()
        try:
            self.run_as_current_user(self.fs.chdir, path)
        except (OSError, FilesystemError) as err:
            why = _strerror(err)
            self.respond('550 %s.' % why)
        else:
            cwd = self.fs.cwd
            assert isinstance(cwd, unicode), cwd
            self.respond('250 "%s" is the current directory.' % cwd)
            if getcwdu() != init_cwd:
                os.chdir(init_cwd)
            return path

    def ftp_CDUP(self, path):
        "a"

        return self.ftp_CWD(path)

    def ftp_SIZE(self, path):
        "a"


        line = self.fs.fs2ftp(path)
        if self._current_type == 'a':
            why = "SIZE not allowed in ASCII mode"
            self.respond("550 %s." % why)
            return
        if not self.fs.isfile(self.fs.realpath(path)):
            why = "%s is not retrievable" % line
            self.respond("550 %s." % why)
            return
        try:
            size = self.run_as_current_user(self.fs.getsize, path)
        except (OSError, FilesystemError) as err:
            why = _strerror(err)
            self.respond('550 %s.' % why)
        else:
            self.respond("213 %s" % size)

    def ftp_MDTM(self, path):
        "a"
        line = self.fs.fs2ftp(path)
        if not self.fs.isfile(self.fs.realpath(path)):
            self.respond("550 %s is not retrievable" % line)
            return
        timefunc = time.gmtime if self.use_gmt_times else time.localtime
        try:
            secs = self.run_as_current_user(self.fs.getmtime, path)
            lmt = time.strftime("%Y%m%d%H%M%S", timefunc(secs))
        except (ValueError, OSError, FilesystemError) as err:
            if isinstance(err, ValueError):

                why = "Can't determine file's last modification time"
            else:
                why = _strerror(err)
            self.respond('550 %s.' % why)
        else:
            self.respond("213 %s" % lmt)
            return path

    def ftp_MFMT(self, path, timeval):
        "a"


        line = self.fs.fs2ftp(path)

        if len(timeval) != len("YYYYMMDDHHMMSS"):
            why = "Invalid time format; expected: YYYYMMDDHHMMSS"
            self.respond('550 %s.' % why)
            return
        if not self.fs.isfile(self.fs.realpath(path)):
            self.respond("550 %s is not retrievable" % line)
            return
        timefunc = time.gmtime if self.use_gmt_times else time.localtime
        try:

            epoch = datetime.utcfromtimestamp(0)
            timeval_datetime_obj = datetime.strptime(timeval, '%Y%m%d%H%M%S')
            timeval_secs = (timeval_datetime_obj - epoch).total_seconds()
        except ValueError:
            why = "Invalid time format; expected: YYYYMMDDHHMMSS"
            self.respond('550 %s.' % why)
            return
        try:

            self.run_as_current_user(self.fs.utime, path, timeval_secs)

            secs = self.run_as_current_user(self.fs.getmtime, path)
            lmt = time.strftime("%Y%m%d%H%M%S", timefunc(secs))
        except (ValueError, OSError, FilesystemError) as err:
            if isinstance(err, ValueError):

                why = "Can't determine file's last modification time"
            else:
                why = _strerror(err)
            self.respond('550 %s.' % why)
        else:
            self.respond("213 Modify=%s; %s." % (lmt, line))
            return (lmt, path)

    def ftp_MKD(self, path):
        "a"
        line = self.fs.fs2ftp(path)
        try:
            self.run_as_current_user(self.fs.mkdir, path)
        except (OSError, FilesystemError) as err:
            why = _strerror(err)
            self.respond('550 %s.' % why)
        else:

            self.respond(
                '257 "%s" directory created.' % line.replace('"', '""')
            )
            return path

    def ftp_RMD(self, path):
        "a"
        if self.fs.realpath(path) == self.fs.realpath(self.fs.root):
            msg = "Can't remove root directory."
            self.respond("550 %s" % msg)
            return
        try:
            self.run_as_current_user(self.fs.rmdir, path)
        except (OSError, FilesystemError) as err:
            why = _strerror(err)
            self.respond('550 %s.' % why)
        else:
            self.respond("250 Directory removed.")

    def ftp_DELE(self, path):
        "a"
        try:
            self.run_as_current_user(self.fs.remove, path)
        except (OSError, FilesystemError) as err:
            why = _strerror(err)
            self.respond('550 %s.' % why)
        else:
            self.respond("250 File removed.")
            return path

    def ftp_RNFR(self, path):
        "a"
        if not self.fs.lexists(path):
            self.respond("550 No such file or directory.")
        elif self.fs.realpath(path) == self.fs.realpath(self.fs.root):
            self.respond("550 Can't rename home directory.")
        else:
            self._rnfr = path
            self.respond("350 Ready for destination name.")

    def ftp_RNTO(self, path):
        "a"
        if not self._rnfr:
            self.respond("503 Bad sequence of commands: use RNFR first.")
            return
        src = self._rnfr
        self._rnfr = None
        try:
            self.run_as_current_user(self.fs.rename, src, path)
        except (OSError, FilesystemError) as err:
            why = _strerror(err)
            self.respond('550 %s.' % why)
        else:
            self.respond("250 Renaming ok.")
            return (src, path)


    def ftp_TYPE(self, line):
        "a"
        type = line.upper().replace(' ', '')
        if type in ("A", "L7"):
            self.respond("200 Type set to: ASCII.")
            self._current_type = 'a'
        elif type in ("I", "L8"):
            self.respond("200 Type set to: Binary.")
            self._current_type = 'i'
        else:
            self.respond('504 Unsupported type "%s".' % line)

    def ftp_STRU(self, line):
        "a"
        stru = line.upper()
        if stru == 'F':
            self.respond('200 File transfer structure set to: F.')
        elif stru in ('P', 'R'):

            self.respond('504 Unimplemented STRU type.')
        else:
            self.respond('501 Unrecognized STRU type.')

    def ftp_MODE(self, line):
        "a"
        mode = line.upper()
        if mode == 'S':
            self.respond('200 Transfer mode set to: S')
        elif mode in ('B', 'C'):
            self.respond('504 Unimplemented MODE type.')
        else:
            self.respond('501 Unrecognized MODE type.')

    def ftp_STAT(self, path):
        "a"

        if not path:
            s = []
            s.append('Connected to: %s:%s' % self.socket.getsockname()[:2])
            if self.authenticated:
                s.append('Logged in as: %s' % self.username)
            else:
                if not self.username:
                    s.append("Waiting for username.")
                else:
                    s.append("Waiting for password.")
            type = 'ASCII' if self._current_type == 'a' else 'Binary'
            s.append("TYPE: %s; STRUcture: File; MODE: Stream" % type)
            if self._dtp_acceptor is not None:
                s.append('Passive data channel waiting for connection.')
            elif self.data_channel is not None:
                bytes_sent = self.data_channel.tot_bytes_sent
                bytes_recv = self.data_channel.tot_bytes_received
                elapsed_time = self.data_channel.get_elapsed_time()
                s.append('Data connection open:')
                s.append('Total bytes sent: %s' % bytes_sent)
                s.append('Total bytes received: %s' % bytes_recv)
                s.append('Transfer elapsed time: %s secs' % elapsed_time)
            else:
                s.append('Data connection closed.')

            self.push('211-FTP server status:\r\n')
            self.push(''.join([' %s\r\n' % item for item in s]))
            self.respond('211 End of status.')

        else:
            line = self.fs.fs2ftp(path)
            try:
                isdir = self.fs.isdir(path)
                if isdir:
                    listing = self.run_as_current_user(self.fs.listdir, path)
                    if isinstance(listing, list):
                        try:

                            listing.sort()
                        except UnicodeDecodeError:

                            pass
                    iterator = self.fs.format_list(path, listing)
                else:
                    basedir, filename = os.path.split(path)
                    self.fs.lstat(path)
                    iterator = self.fs.format_list(basedir, [filename])
            except (OSError, FilesystemError) as err:
                why = _strerror(err)
                self.respond('550 %s.' % why)
            else:
                self.push('213-Status of "%s":\r\n' % line)
                self.push_with_producer(BufferedIteratorProducer(iterator))
                self.respond('213 End of status.')
                return path

    def ftp_FEAT(self, line):
        "a"
        features = set(['UTF8', 'TVFS'])
        features.update(
            [
                feat
                for feat in ('EPRT', 'EPSV', 'MDTM', 'MFMT', 'SIZE')
                if feat in self.proto_cmds
            ]
        )
        features.update(self._extra_feats)
        if 'MLST' in self.proto_cmds or 'MLSD' in self.proto_cmds:
            facts = ''
            for fact in self._available_facts:
                if fact in self._current_facts:
                    facts += fact + '*;'
                else:
                    facts += fact + ';'
            features.add('MLST ' + facts)
        if 'REST' in self.proto_cmds:
            features.add('REST STREAM')
        features = sorted(features)
        self.push("211-Features supported:\r\n")
        self.push("".join([" %s\r\n" % x for x in features]))
        self.respond('211 End FEAT.')

    def ftp_OPTS(self, line):
        "a"
        try:
            if line.count(' ') > 1:
                raise ValueError('Invalid number of arguments')
            if ' ' in line:
                cmd, arg = line.split(' ')
                if ';' not in arg:
                    raise ValueError('Invalid argument')
            else:
                cmd, arg = line, ''

            if cmd.upper() != 'MLST' or 'MLST' not in self.proto_cmds:
                raise ValueError('Unsupported command "%s"' % cmd)
        except ValueError as err:
            self.respond('501 %s.' % err)
        else:
            facts = [x.lower() for x in arg.split(';')]
            self._current_facts = [
                x for x in facts if x in self._available_facts
            ]
            f = ''.join([x + ';' for x in self._current_facts])
            self.respond('200 MLST OPTS ' + f)

    def ftp_NOOP(self, line):
        "a"
        self.respond("200 I successfully did nothing'.")

    def ftp_SYST(self, line):
        "a"

        self.respond("215 UNIX Type: L8")

    def ftp_ALLO(self, line):
        "a"

        self.respond("202 No storage allocation necessary.")

    def ftp_HELP(self, line):
        "a"
        if line:
            line = line.upper()
            if line in self.proto_cmds:
                self.respond("214 %s" % self.proto_cmds[line]['help'])
            else:
                self.respond("501 Unrecognized command.")
        else:

            def formatted_help():
                cmds = []
                keys = sorted(
                    [x for x in self.proto_cmds if not x.startswith('SITE ')]
                )
                while keys:
                    elems = tuple(keys[0:8])
                    cmds.append(' %-6s' * len(elems) % elems + '\r\n')
                    del keys[0:8]
                return ''.join(cmds)

            self.push("214-The following commands are recognized:\r\n")
            self.push(formatted_help())
            self.respond("214 Help command successful.")


    def ftp_SITE_CHMOD(self, path, mode):
        "a"

        try:
            assert len(mode) in (3, 4)
            for x in mode:
                assert 0 <= int(x) <= 7
            mode = int(mode, 8)
        except (AssertionError, ValueError):
            self.respond("501 Invalid SITE CHMOD format.")
        else:
            try:
                self.run_as_current_user(self.fs.chmod, path, mode)
            except (OSError, FilesystemError) as err:
                why = _strerror(err)
                self.respond('550 %s.' % why)
            else:
                self.respond('200 SITE CHMOD successful.')
                return (path, mode)

    def ftp_SITE_HELP(self, line):
        "a"
        if line:
            line = line.upper()
            if line in self.proto_cmds:
                self.respond("214 %s" % self.proto_cmds[line]['help'])
            else:
                self.respond("501 Unrecognized SITE command.")
        else:
            self.push("214-The following SITE commands are recognized:\r\n")
            site_cmds = []
            for cmd in sorted(self.proto_cmds.keys()):
                if cmd.startswith('SITE '):
                    site_cmds.append(' %s\r\n' % cmd[5:])
            self.push(''.join(site_cmds))
            self.respond("214 Help SITE command successful.")


    def ftp_XCUP(self, line):
        "a"
        return self.ftp_CDUP(line)

    def ftp_XCWD(self, line):
        "a"
        return self.ftp_CWD(line)

    def ftp_XMKD(self, line):
        "a"
        return self.ftp_MKD(line)

    def ftp_XPWD(self, line):
        "a"
        return self.ftp_PWD(line)

    def ftp_XRMD(self, line):
        "a"
        return self.ftp_RMD(line)



if SSL is not None:

    class SSLConnection(_AsyncChatNewStyle):
        "a"

        _ssl_accepting = False
        _ssl_established = False
        _ssl_closing = False
        _ssl_requested = False

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._error = False
            self._ssl_want_read = False
            self._ssl_want_write = False

        def readable(self):
            return (
                self._ssl_accepting
                or self._ssl_want_read
                or super().readable()
            )

        def writable(self):
            return self._ssl_want_write or super().writable()

        def secure_connection(self, ssl_context):
            "a"
            debug("securing SSL connection", self)
            self._ssl_requested = True
            try:
                self.socket = SSL.Connection(ssl_context, self.socket)
            except socket.error as err:

                debug(
                    "call: secure_connection(); can't secure SSL connection "
                    "%r; closing" % err,
                    self,
                )
                self.close()
            except ValueError:

                if self.socket.fileno() == -1:
                    debug(
                        "ValueError and fd == -1 on secure_connection()", self
                    )
                    return
                raise
            else:
                self.socket.set_accept_state()
                self._ssl_accepting = True

        @contextlib.contextmanager
        def _handle_ssl_want_rw(self):
            prev_row_pending = self._ssl_want_read or self._ssl_want_write
            try:
                yield
            except SSL.WantReadError:

                self._ssl_want_read = True
            except SSL.WantWriteError:

                self._ssl_want_write = True

            if self._ssl_want_read:
                self.modify_ioloop_events(
                    self._wanted_io_events | self.ioloop.READ, logdebug=True
                )
            elif self._ssl_want_write:
                self.modify_ioloop_events(
                    self._wanted_io_events | self.ioloop.WRITE, logdebug=True
                )
            else:
                if prev_row_pending:
                    self.modify_ioloop_events(self._wanted_io_events)

        def _do_ssl_handshake(self):
            self._ssl_accepting = True
            self._ssl_want_read = False
            self._ssl_want_write = False
            try:
                self.socket.do_handshake()
            except SSL.WantReadError:
                self._ssl_want_read = True
                debug("call: _do_ssl_handshake, err: ssl-want-read", inst=self)
            except SSL.WantWriteError:
                self._ssl_want_write = True
                debug(
                    "call: _do_ssl_handshake, err: ssl-want-write", inst=self
                )
            except SSL.SysCallError as err:
                debug("call: _do_ssl_handshake, err: %r" % err, inst=self)
                retval, desc = err.args
                if (retval == -1 and desc == 'Unexpected EOF') or retval > 0:

                    self.log("Unexpected SSL EOF.")
                    self.close()
                else:
                    raise
            except SSL.Error as err:
                debug("call: _do_ssl_handshake, err: %r" % err, inst=self)
                self.handle_failed_ssl_handshake()
            else:
                debug("SSL connection established", self)
                self._ssl_accepting = False
                self._ssl_established = True
                self.handle_ssl_established()

        def handle_ssl_established(self):
            "a"

        def handle_ssl_shutdown(self):
            "a"
            super().close()

        def handle_failed_ssl_handshake(self):
            raise NotImplementedError("must be implemented in subclass")

        def handle_read_event(self):
            if not self._ssl_requested:
                super().handle_read_event()
            else:
                with self._handle_ssl_want_rw():
                    self._ssl_want_read = False
                    if self._ssl_accepting:
                        self._do_ssl_handshake()
                    elif self._ssl_closing:
                        self._do_ssl_shutdown()
                    else:
                        super().handle_read_event()

        def handle_write_event(self):
            if not self._ssl_requested:
                super().handle_write_event()
            else:
                with self._handle_ssl_want_rw():
                    self._ssl_want_write = False
                    if self._ssl_accepting:
                        self._do_ssl_handshake()
                    elif self._ssl_closing:
                        self._do_ssl_shutdown()
                    else:
                        super().handle_write_event()

        def handle_error(self):
            self._error = True
            try:
                raise
            except Exception:
                self.log_exception(self)

            try:
                super().close()
            except Exception:
                logger.critical(traceback.format_exc())

        def send(self, data):
            if not isinstance(data, bytes):
                data = bytes(data)
            try:
                return super().send(data)
            except SSL.WantReadError:
                debug("call: send(), err: ssl-want-read", inst=self)
                self._ssl_want_read = True
                return 0
            except SSL.WantWriteError:
                debug("call: send(), err: ssl-want-write", inst=self)
                self._ssl_want_write = True
                return 0
            except SSL.ZeroReturnError:
                debug(
                    "call: send() -> shutdown(), err: zero-return", inst=self
                )
                super().handle_close()
                return 0
            except SSL.SysCallError as err:
                debug("call: send(), err: %r" % err, inst=self)
                errnum, errstr = err.args
                if errnum == errno.EWOULDBLOCK:
                    return 0
                elif (
                    errnum in _ERRNOS_DISCONNECTED
                    or errstr == 'Unexpected EOF'
                ):
                    super().handle_close()
                    return 0
                else:
                    raise

        def recv(self, buffer_size):
            try:
                return super().recv(buffer_size)
            except SSL.WantReadError:
                debug("call: recv(), err: ssl-want-read", inst=self)
                self._ssl_want_read = True
                raise RetryError
            except SSL.WantWriteError:
                debug("call: recv(), err: ssl-want-write", inst=self)
                self._ssl_want_write = True
                raise RetryError
            except SSL.ZeroReturnError:
                debug(
                    "call: recv() -> shutdown(), err: zero-return", inst=self
                )
                super().handle_close()
                return b''
            except SSL.SysCallError as err:
                debug("call: recv(), err: %r" % err, inst=self)
                errnum, errstr = err.args
                if (
                    errnum in _ERRNOS_DISCONNECTED
                    or errstr == 'Unexpected EOF'
                ):
                    super().handle_close()
                    return b''
                else:
                    raise

        def _do_ssl_shutdown(self):
            "a"
            self._ssl_closing = True
            if os.name == 'posix':

                try:
                    os.write(self.socket.fileno(), b'')
                except (OSError, socket.error) as err:
                    debug(
                        "call: _do_ssl_shutdown() -> os.write, err: %r" % err,
                        inst=self,
                    )
                    if err.errno in {
                        errno.EINTR,
                        errno.EWOULDBLOCK,
                        errno.ENOBUFS,
                    }:
                        return
                    elif err.errno in _ERRNOS_DISCONNECTED:
                        return super().close()
                    else:
                        raise

            try:
                laststate = self.socket.get_shutdown()
                self.socket.set_shutdown(laststate | SSL.RECEIVED_SHUTDOWN)
                done = self.socket.shutdown()
                if not laststate & SSL.RECEIVED_SHUTDOWN:
                    self.socket.set_shutdown(SSL.SENT_SHUTDOWN)
            except SSL.WantReadError:
                self._ssl_want_read = True
                debug("call: _do_ssl_shutdown, err: ssl-want-read", inst=self)
            except SSL.WantWriteError:
                self._ssl_want_write = True
                debug("call: _do_ssl_shutdown, err: ssl-want-write", inst=self)
            except SSL.ZeroReturnError:
                debug(
                    "call: _do_ssl_shutdown() -> shutdown(), err: zero-return",
                    inst=self,
                )
                super().close()
            except SSL.SysCallError as err:
                debug(
                    "call: _do_ssl_shutdown() -> shutdown(), err: %r" % err,
                    inst=self,
                )
                errnum, errstr = err.args
                if (
                    errnum in _ERRNOS_DISCONNECTED
                    or errstr == 'Unexpected EOF'
                ):
                    super().close()
                else:
                    raise
            except SSL.Error as err:
                debug(
                    "call: _do_ssl_shutdown() -> shutdown(), err: %r" % err,
                    inst=self,
                )

                if err.args and not getattr(err, "errno", None):
                    pass
                else:
                    raise
            except socket.error as err:
                debug(
                    "call: _do_ssl_shutdown() -> shutdown(), err: %r" % err,
                    inst=self,
                )
                if err.errno in _ERRNOS_DISCONNECTED:
                    super().close()
                else:
                    raise
            else:
                if done:
                    debug(
                        "call: _do_ssl_shutdown(), shutdown completed",
                        inst=self,
                    )
                    self._ssl_established = False
                    self._ssl_closing = False
                    self.handle_ssl_shutdown()
                else:
                    debug(
                        "call: _do_ssl_shutdown(), shutdown not completed yet",
                        inst=self,
                    )

        def close(self):
            if self._ssl_established and not self._error:
                self._do_ssl_shutdown()
            else:
                self._ssl_accepting = False
                self._ssl_established = False
                self._ssl_closing = False
                super().close()

    class TLS_DTPHandler(SSLConnection, DTPHandler):
        "a"

        def __init__(self, sock, cmd_channel):
            super().__init__(sock, cmd_channel)
            if self.cmd_channel._prot:
                self.secure_connection(self.cmd_channel.ssl_context)

        def __repr__(self):
            return DTPHandler.__repr__(self)

        def use_sendfile(self):
            if isinstance(self.socket, SSL.Connection):
                return False
            else:
                return super().use_sendfile()

        def handle_failed_ssl_handshake(self):

            self.cmd_channel.respond("522 SSL handshake failed.")
            self.cmd_channel.log_cmd("PROT", "P", 522, "SSL handshake failed.")
            self.close()

    class TLS_FTPHandler(SSLConnection, FTPHandler):
        "a"

        tls_control_required = False
        tls_data_required = False
        certfile = None
        keyfile = None
        ssl_protocol = SSL.SSLv23_METHOD

        ssl_options = SSL.OP_NO_SSLv2 | SSL.OP_NO_SSLv3
        if hasattr(SSL, "OP_NO_COMPRESSION"):
            ssl_options |= SSL.OP_NO_COMPRESSION
        ssl_context = None

        dtp_handler = TLS_DTPHandler
        proto_cmds = FTPHandler.proto_cmds.copy()
        proto_cmds.update(
            {
                'AUTH': dict(
                    perm=None,
                    auth=False,
                    arg=True,
                    help=(
                        'Syntax: AUTH <SP> TLS|SSL (set up secure control '
                        'channel).'
                    ),
                ),
                'PBSZ': dict(
                    perm=None,
                    auth=False,
                    arg=True,
                    help='Syntax: PBSZ <SP> 0 (negotiate TLS buffer).',
                ),
                'PROT': dict(
                    perm=None,
                    auth=False,
                    arg=True,
                    help=(
                        'Syntax: PROT <SP> [C|P] (set up un/secure data'
                        ' channel).'
                    ),
                ),
            }
        )

        def __init__(self, conn, server, ioloop=None):
            super().__init__(conn, server, ioloop)
            if not self.connected:
                return
            self._extra_feats = ['AUTH TLS', 'AUTH SSL', 'PBSZ', 'PROT']
            self._pbsz = False
            self._prot = False
            self.ssl_context = self.get_ssl_context()

        def __repr__(self):
            return FTPHandler.__repr__(self)

        @classmethod
        def get_ssl_context(cls):
            if cls.ssl_context is None:
                if cls.certfile is None:
                    raise ValueError("at least certfile must be specified")
                cls.ssl_context = SSL.Context(cls.ssl_protocol)
                cls.ssl_context.use_certificate_chain_file(cls.certfile)
                if not cls.keyfile:
                    cls.keyfile = cls.certfile
                cls.ssl_context.use_privatekey_file(cls.keyfile)
                if cls.ssl_options:
                    cls.ssl_context.set_options(cls.ssl_options)
            return cls.ssl_context


        def flush_account(self):
            FTPHandler.flush_account(self)
            self._pbsz = False
            self._prot = False

        def process_command(self, cmd, *args, **kwargs):
            if cmd in ('USER', 'PASS'):
                if self.tls_control_required and not self._ssl_established:
                    msg = "SSL/TLS required on the control channel."
                    self.respond("550 " + msg)
                    self.log_cmd(cmd, args[0], 550, msg)
                    return
            elif cmd in ('PASV', 'EPSV', 'PORT', 'EPRT'):
                if self.tls_data_required and not self._prot:
                    msg = "SSL/TLS required on the data channel."
                    self.respond("550 " + msg)
                    self.log_cmd(cmd, args[0], 550, msg)
                    return
            FTPHandler.process_command(self, cmd, *args, **kwargs)

        def close(self):
            SSLConnection.close(self)
            FTPHandler.close(self)


        def handle_failed_ssl_handshake(self):

            self.log("SSL handshake failed.")
            self.close()

        def ftp_AUTH(self, line):
            "a"
            arg = line.upper()
            if isinstance(self.socket, SSL.Connection):
                self.respond("503 Already using TLS.")
            elif arg in ('TLS', 'TLS-C', 'SSL', 'TLS-P'):

                self.respond('234 AUTH %s successful.' % arg)
                self.secure_connection(self.ssl_context)
            else:
                self.respond(
                    "502 Unrecognized encryption type (use TLS or SSL)."
                )

        def ftp_PBSZ(self, line):
            "a"
            if not isinstance(self.socket, SSL.Connection):
                self.respond(
                    "503 PBSZ not allowed on insecure control connection."
                )
            else:
                self.respond('200 PBSZ=0 successful.')
                self._pbsz = True

        def ftp_PROT(self, line):
            "a"
            arg = line.upper()
            if not isinstance(self.socket, SSL.Connection):
                self.respond(
                    "503 PROT not allowed on insecure control connection."
                )
            elif not self._pbsz:
                self.respond(
                    "503 You must issue the PBSZ command prior to PROT."
                )
            elif arg == 'C':
                self.respond('200 Protection set to Clear')
                self._prot = False
            elif arg == 'P':
                self.respond('200 Protection set to Private')
                self._prot = True
            elif arg in ('S', 'E'):
                self.respond('521 PROT %s unsupported (use C or P).' % arg)
            else:
                self.respond("502 Unrecognized PROT type (use C or P).")
