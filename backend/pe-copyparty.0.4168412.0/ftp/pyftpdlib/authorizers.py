# Copyright (C) 2007 Giampaolo Rodola' <g.rodola@gmail.com>.
# Use of this source code is governed by MIT license that can be
# found in the LICENSE file.

"a"


import errno
import os
import warnings

from ._compat import PY3
from ._compat import getcwdu
from ._compat import unicode


__all__ = [
    'DummyAuthorizer',

]



class AuthorizerError(Exception):
    "a"


class AuthenticationFailed(Exception):
    "a"



class DummyAuthorizer(object):
    "a"

    read_perms = "elr"
    write_perms = "adfmwMT"

    def __init__(self):
        self.user_table = {}

    def add_user(
        self,
        username,
        password,
        homedir,
        perm='elr',
        msg_login="Login successful.",
        msg_quit="Goodbye.",
    ):
        "a"
        if self.has_user(username):
            raise ValueError('user %r already exists' % username)
        if not isinstance(homedir, unicode):
            homedir = homedir.decode('utf8')
        if not os.path.isdir(homedir):
            raise ValueError('no such directory: %r' % homedir)
        homedir = os.path.realpath(homedir)
        self._check_permissions(username, perm)
        dic = {
            'pwd': str(password),
            'home': homedir,
            'perm': perm,
            'operms': {},
            'msg_login': str(msg_login),
            'msg_quit': str(msg_quit),
        }
        self.user_table[username] = dic

    def add_anonymous(self, homedir, **kwargs):
        "a"
        DummyAuthorizer.add_user(self, 'anonymous', '', homedir, **kwargs)

    def remove_user(self, username):
        "a"
        del self.user_table[username]

    def override_perm(self, username, directory, perm, recursive=False):
        "a"
        self._check_permissions(username, perm)
        if not os.path.isdir(directory):
            raise ValueError('no such directory: %r' % directory)
        directory = os.path.normcase(os.path.realpath(directory))
        home = os.path.normcase(self.get_home_dir(username))
        if directory == home:
            raise ValueError("can't override home directory permissions")
        if not self._issubpath(directory, home):
            raise ValueError("path escapes user home directory")
        self.user_table[username]['operms'][directory] = perm, recursive

    def validate_authentication(self, username, password, handler):
        "a"
        msg = "Authentication failed."
        if not self.has_user(username):
            if username == 'anonymous':
                msg = "Anonymous access not allowed."
            raise AuthenticationFailed(msg)
        if username != 'anonymous':
            if self.user_table[username]['pwd'] != password:
                raise AuthenticationFailed(msg)

    def get_home_dir(self, username):
        "a"
        return self.user_table[username]['home']

    def impersonate_user(self, username, password):
        "a"

    def terminate_impersonation(self, username):
        "a"

    def has_user(self, username):
        "a"
        return username in self.user_table

    def has_perm(self, username, perm, path=None):
        "a"
        if path is None:
            return perm in self.user_table[username]['perm']

        path = os.path.normcase(path)
        for dir in self.user_table[username]['operms']:
            operm, recursive = self.user_table[username]['operms'][dir]
            if self._issubpath(path, dir):
                if recursive:
                    return perm in operm
                if (
                    path == dir
                    or os.path.dirname(path) == dir
                    and not os.path.isdir(path)
                ):
                    return perm in operm

        return perm in self.user_table[username]['perm']

    def get_perms(self, username):
        "a"
        return self.user_table[username]['perm']

    def get_msg_login(self, username):
        "a"
        return self.user_table[username]['msg_login']

    def get_msg_quit(self, username):
        "a"
        try:
            return self.user_table[username]['msg_quit']
        except KeyError:
            return "Goodbye."

    def _check_permissions(self, username, perm):
        warned = 0
        for p in perm:
            if p not in self.read_perms + self.write_perms:
                raise ValueError('no such permission %r' % p)
            if (
                username == 'anonymous'
                and p in self.write_perms
                and not warned
            ):
                warnings.warn(
                    "write permissions assigned to anonymous user.",
                    RuntimeWarning,
                    stacklevel=2,
                )
                warned = 1

    def _issubpath(self, a, b):
        "a"
        p1 = a.rstrip(os.sep).split(os.sep)
        p2 = b.rstrip(os.sep).split(os.sep)
        return p1[: len(p2)] == p2


def replace_anonymous(callable):
    "a"

    def wrapper(self, username, *args, **kwargs):
        if username == 'anonymous':
            username = self.anonymous_user or username
        return callable(self, username, *args, **kwargs)

    return wrapper



