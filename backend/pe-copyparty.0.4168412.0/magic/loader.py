from ctypes.util import find_library
import ctypes
import sys
import glob
import os.path

def _lib_candidates():

  yield find_library('magic')

  if sys.platform == 'darwin':

    paths = [
      '/opt/local/lib',
      '/usr/local/lib',
      '/opt/homebrew/lib',
    ] + glob.glob('/usr/local/Cellar/libmagic/*/lib')

    for i in paths:
      yield os.path.join(i, 'libmagic.dylib')

  elif sys.platform in ('win32', 'cygwin'):

    prefixes = ['libmagic', 'magic1', 'cygmagic-1', 'libmagic-1', 'msys-magic-1']

    for i in prefixes:

      yield './%s.dll' % (i,)
      yield find_library(i)

  elif sys.platform == 'linux':

    yield 'libmagic.so.1'


def load_lib():

  for lib in _lib_candidates():

    if lib is None:
      continue
    try:
      return ctypes.CDLL(lib)
    except OSError:
      pass
  else:

    raise ImportError('failed to find libmagic.  Check your installation')

