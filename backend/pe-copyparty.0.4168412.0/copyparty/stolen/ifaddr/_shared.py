# coding: utf-8
from __future__ import print_function, unicode_literals

import ctypes
import platform
import socket
import sys

import ipaddress

PY2 = sys.version_info < (3,)
if not PY2:
    U   = str
else:
    U = unicode
    range = xrange


class Adapter(object):
    "a"

    def __init__(
        self, name , nice_name , ips , index  = None
    )  :

        self.name = name

        self.nice_name = nice_name

        self.ips = ips

        self.index = index

    def __repr__(self)  :
        return "Adapter(name={name}, nice_name={nice_name}, ips={ips}, index={index})".format(
            name=repr(self.name),
            nice_name=repr(self.nice_name),
            ips=repr(self.ips),
            index=repr(self.index),
        )


class IP(object):
    "a"

    def __init__(
        self, ip  , network_prefix , nice_name 
    )  :

        self.ip = ip

        self.network_prefix = network_prefix

        self.nice_name = nice_name

    @property
    def is_IPv4(self)  :
        "a"
        return not isinstance(self.ip, tuple)

    @property
    def is_IPv6(self)  :
        "a"
        return isinstance(self.ip, tuple)

    def __repr__(self)  :
        return "IP(ip={ip}, network_prefix={network_prefix}, nice_name={nice_name})".format(
            ip=repr(self.ip),
            network_prefix=repr(self.network_prefix),
            nice_name=repr(self.nice_name),
        )


if platform.system() == "Darwin" or "BSD" in platform.system():


    class sockaddr(ctypes.Structure):
        _fields_ = [
            ("sa_len", ctypes.c_uint8),
            ("sa_familiy", ctypes.c_uint8),
            ("sa_data", ctypes.c_uint8 * 14),
        ]

    class sockaddr_in(ctypes.Structure):
        _fields_ = [
            ("sa_len", ctypes.c_uint8),
            ("sa_familiy", ctypes.c_uint8),
            ("sin_port", ctypes.c_uint16),
            ("sin_addr", ctypes.c_uint8 * 4),
            ("sin_zero", ctypes.c_uint8 * 8),
        ]

    class sockaddr_in6(ctypes.Structure):
        _fields_ = [
            ("sa_len", ctypes.c_uint8),
            ("sa_familiy", ctypes.c_uint8),
            ("sin6_port", ctypes.c_uint16),
            ("sin6_flowinfo", ctypes.c_uint32),
            ("sin6_addr", ctypes.c_uint8 * 16),
            ("sin6_scope_id", ctypes.c_uint32),
        ]

else:

    class sockaddr(ctypes.Structure):
        _fields_ = [("sa_familiy", ctypes.c_uint16), ("sa_data", ctypes.c_uint8 * 14)]

    class sockaddr_in(ctypes.Structure):
        _fields_ = [
            ("sin_familiy", ctypes.c_uint16),
            ("sin_port", ctypes.c_uint16),
            ("sin_addr", ctypes.c_uint8 * 4),
            ("sin_zero", ctypes.c_uint8 * 8),
        ]

    class sockaddr_in6(ctypes.Structure):
        _fields_ = [
            ("sin6_familiy", ctypes.c_uint16),
            ("sin6_port", ctypes.c_uint16),
            ("sin6_flowinfo", ctypes.c_uint32),
            ("sin6_addr", ctypes.c_uint8 * 16),
            ("sin6_scope_id", ctypes.c_uint32),
        ]


def sockaddr_to_ip(
    sockaddr_ptr ,
)   :
    if sockaddr_ptr:
        if sockaddr_ptr[0].sa_familiy == socket.AF_INET:
            ipv4 = ctypes.cast(sockaddr_ptr, ctypes.POINTER(sockaddr_in))
            ippacked = bytes(bytearray(ipv4[0].sin_addr))
            ip = U(ipaddress.ip_address(ippacked))
            return ip
        elif sockaddr_ptr[0].sa_familiy == socket.AF_INET6:
            ipv6 = ctypes.cast(sockaddr_ptr, ctypes.POINTER(sockaddr_in6))
            flowinfo = ipv6[0].sin6_flowinfo
            ippacked = bytes(bytearray(ipv6[0].sin6_addr))
            ip = U(ipaddress.ip_address(ippacked))
            scope_id = ipv6[0].sin6_scope_id
            return (ip, flowinfo, scope_id)
    return None


def ipv6_prefixlength(address )  :
    prefix_length = 0
    for i in range(address.max_prefixlen):
        if int(address) >> i & 1:
            prefix_length = prefix_length + 1
    return prefix_length
