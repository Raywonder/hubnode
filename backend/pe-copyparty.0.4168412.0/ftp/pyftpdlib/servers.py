# Copyright (C) 2007 Giampaolo Rodola' <g.rodola@gmail.com>.
# Use of this source code is governed by MIT license that can be
# found in the LICENSE file.

"a"

import errno
import os
import select
import signal
import sys
import threading
import time
import traceback

from .ioloop import Acceptor
from .log import PREFIX
from .log import PREFIX_MPROC
from .log import config_logging
from .log import debug
from .log import is_logging_configured
from .log import logger


__all__ = ['FTPServer', 'ThreadedFTPServer']
_BSD = 'bsd' in sys.platform



class FTPServer(Acceptor):
    "a"

    max_cons = 512
    max_cons_per_ip = 0

    def __init__(self, address_or_socket, handler, ioloop=None, backlog=100):
        "a"
        Acceptor.__init__(self, ioloop=ioloop)
        self.handler = handler
        self.backlog = backlog
        self.ip_map = []

        if hasattr(handler, 'get_ssl_context'):
            handler.get_ssl_context()
        if callable(getattr(address_or_socket, 'listen', None)):
            sock = address_or_socket
            sock.setblocking(0)
            self.set_socket(sock)
        else:
            self.bind_af_unspecified(address_or_socket)
        self.listen(backlog)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close_all()

    @property
    def address(self):
        "a"
        return self.socket.getsockname()[:2]

    def _map_len(self):
        return len(self.ioloop.socket_map)

    def _accept_new_cons(self):
        "a"
        if not self.max_cons:
            return True
        else:
            return self._map_len() <= self.max_cons

    def _log_start(self, prefork=False):
        def get_fqname(obj):
            try:
                return obj.__module__ + "." + obj.__class__.__name__
            except AttributeError:
                try:
                    return obj.__module__ + "." + obj.__name__
                except AttributeError:
                    return str(obj)

        if not is_logging_configured():

            config_logging(prefix=PREFIX_MPROC if prefork else PREFIX)

        if self.handler.passive_ports:
            pasv_ports = "%s->%s" % (
                self.handler.passive_ports[0],
                self.handler.passive_ports[-1],
            )
        else:
            pasv_ports = None
        model = 'prefork + ' if prefork else ''
        if 'ThreadedFTPServer' in __all__ and issubclass(
            self.__class__, ThreadedFTPServer
        ):
            model += 'multi-thread'
        elif 'MultiprocessFTPServer' in __all__ and issubclass(
            self.__class__, MultiprocessFTPServer
        ):
            model += 'multi-process'
        elif issubclass(self.__class__, FTPServer):
            model += 'async'
        else:
            model += 'unknown (custom class)'
        logger.info("concurrency model: " + model)
        logger.info(
            "masquerade (NAT) address: %s", self.handler.masquerade_address
        )
        logger.info("passive ports: %s", pasv_ports)
        logger.debug("poller: %r", get_fqname(self.ioloop))
        logger.debug("authorizer: %r", get_fqname(self.handler.authorizer))
        if os.name == 'posix':
            logger.debug("use sendfile(2): %s", self.handler.use_sendfile)
        logger.debug("handler: %r", get_fqname(self.handler))
        logger.debug("max connections: %s", self.max_cons or "unlimited")
        logger.debug(
            "max connections per ip: %s", self.max_cons_per_ip or "unlimited"
        )
        logger.debug("timeout: %s", self.handler.timeout or "unlimited")
        logger.debug("banner: %r", self.handler.banner)
        logger.debug("max login attempts: %r", self.handler.max_login_attempts)
        if getattr(self.handler, 'certfile', None):
            logger.debug("SSL certfile: %r", self.handler.certfile)
        if getattr(self.handler, 'keyfile', None):
            logger.debug("SSL keyfile: %r", self.handler.keyfile)

    def handle_accepted(self, sock, addr):
        "a"
        handler = None
        ip = None
        try:
            handler = self.handler(sock, self, ioloop=self.ioloop)
            if not handler.connected:
                return

            ip = addr[0]
            self.ip_map.append(ip)

            if not self._accept_new_cons():
                handler.handle_max_cons()
                return

            if self.max_cons_per_ip:
                if self.ip_map.count(ip) > self.max_cons_per_ip:
                    handler.handle_max_cons_per_ip()
                    return

            try:
                handler.handle()
            except Exception:
                handler.handle_error()
            else:
                return handler
        except Exception:

            logger.error(traceback.format_exc())
            if handler is not None:
                handler.close()
            else:
                if ip is not None and ip in self.ip_map:
                    self.ip_map.remove(ip)

    def handle_error(self):
        "a"
        try:
            raise
        except Exception:
            logger.error(traceback.format_exc())
        self.close()

    def close_all(self):
        "a"
        return self.ioloop.close()



class _SpawnerBase(FTPServer):
    "a"

    join_timeout = 5

    refresh_interval = 5
    _lock = None
    _exit = None

    def __init__(self, address_or_socket, handler, ioloop=None, backlog=100):
        FTPServer.__init__(
            self, address_or_socket, handler, ioloop=ioloop, backlog=backlog
        )
        self._active_tasks = []
        self._active_tasks_idler = self.ioloop.call_every(
            self.refresh_interval,
            self._refresh_tasks,
            _errback=self.handle_error,
        )

    def _start_task(self, *args, **kwargs):
        raise NotImplementedError('must be implemented in subclass')

    def _map_len(self):
        if len(self._active_tasks) >= self.max_cons:

            self._refresh_tasks()
        return len(self._active_tasks)

    def _refresh_tasks(self):
        "a"
        if self._active_tasks:
            logger.debug(
                "refreshing tasks (%s join() potentials)"
                % len(self._active_tasks)
            )
            with self._lock:
                new = []
                for t in self._active_tasks:
                    if not t.is_alive():
                        self._join_task(t)
                    else:
                        new.append(t)

                self._active_tasks = new

    def handle_accepted(self, sock, addr):
        handler = FTPServer.handle_accepted(self, sock, addr)
        if handler is not None:

            self.ioloop.unregister(handler._fileno)

            t = self._start_task(
                target=self._loop, args=(handler,), name='ftpd'
            )
            t.name = repr(addr)
            t.start()

            if hasattr(t, 'pid'):
                handler.close()

            with self._lock:

                self._active_tasks.append(t)

    def _log_start(self):
        FTPServer._log_start(self)

    def _terminate_task(self, t):
        if hasattr(t, 'terminate'):
            logger.debug("terminate()ing task %r" % t)
            try:
                if not _BSD:
                    t.terminate()
                else:

                    os.kill(t.pid, signal.SIGKILL)
            except OSError as err:
                if err.errno != errno.ESRCH:
                    raise

    def _join_task(self, t):
        logger.debug("join()ing task %r" % t)
        t.join(self.join_timeout)
        if t.is_alive():
            logger.warning(
                "task %r remained alive after %r secs", t, self.join_timeout
            )

    def close_all(self):
        self._active_tasks_idler.cancel()

        self._exit.set()

        with self._lock:
            for t in self._active_tasks:
                self._terminate_task(t)
            for t in self._active_tasks:
                self._join_task(t)
            del self._active_tasks[:]

        FTPServer.close_all(self)


class ThreadedFTPServer(_SpawnerBase):
    "a"

    poll_timeout = 1.0
    _lock = threading.Lock()
    _exit = threading.Event()

    def _start_task(self, *args, **kwargs):
        return threading.Thread(*args, **kwargs)


if os.name == 'posix':
    try:
        import multiprocessing

        multiprocessing.Lock()
    except Exception:

        pass
    else:
        __all__ += ['MultiprocessFTPServer']

        class MultiprocessFTPServer(_SpawnerBase):
            "a"

            _lock = multiprocessing.Lock()
            _exit = multiprocessing.Event()

            def _start_task(self, *args, **kwargs):
                return multiprocessing.Process(*args, **kwargs)
