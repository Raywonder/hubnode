# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import platform
import sys
import time

_=(0,0)


try:
    TYPE_CHECKING = False
except:
    TYPE_CHECKING = False

PY2 = sys.version_info < (3,)
PY36 = sys.version_info > (3, 6)
if not PY2:
    unicode   = str
else:
    sys.dont_write_bytecode = True
    unicode = unicode

WINDOWS  = (
    [int(x) for x in platform.version().split(".")]
    if platform.system() == "Windows"
    else False
)

VT100 = "--ansi" in sys.argv or (
    os.environ.get("NO_COLOR", "").lower() in ("", "0", "false")
    and sys.stdout.isatty()
    and "--no-ansi" not in sys.argv
    and (not WINDOWS or WINDOWS >= [10, 0, 14393])
)


ANYWIN = WINDOWS or sys.platform in ["msys", "cygwin"]

MACOS = platform.system() == "Darwin"

EXE = bool(getattr(sys, "frozen", False))

try:
    CORES = len(os.sched_getaffinity(0))
except:
    CORES = (os.cpu_count() if hasattr(os, "cpu_count") else 0) or 2

zs = """
web/a/partyfuse.py
web/a/u2c.py
web/a/webdav-cfg.bat
web/baguettebox.js
web/browser.css
web/browser.html
web/browser.js
web/browser2.html
web/cf.html
web/copyparty.gif
web/deps/busy.mp3
web/deps/easymde.css
web/deps/easymde.js
web/deps/marked.js
web/deps/fuse.py
web/deps/mini-fa.css
web/deps/mini-fa.woff
web/deps/prism.css
web/deps/prism.js
web/deps/prismd.css
web/deps/scp.woff2
web/deps/sha512.ac.js
web/deps/sha512.hw.js
web/idp.html
web/iiam.gif
web/md.css
web/md.html
web/md.js
web/md2.css
web/md2.js
web/mde.css
web/mde.html
web/mde.js
web/msg.css
web/msg.html
web/rups.css
web/rups.html
web/rups.js
web/shares.css
web/shares.html
web/shares.js
web/splash.css
web/splash.html
web/splash.js
web/svcs.html
web/svcs.js
web/ui.css
web/up2k.js
web/util.js
web/w.hash.js
"""
RES = set(zs.strip().split("\n"))


class EnvParams(object):
    def __init__(self)  :
        self.t0 = time.time()
        self.mod = ""
        self.mod_ = ""
        self.cfg = ""
        self.scfg = True


E = EnvParams()
