#! /usr/bin/python

"""Display information about the active Python environment.

Compatibility: Python >=2.4 (including Python 3.x).

TODO(pts): Make it work with MicroPython.

The output is sorted (so its order is deterministic).

If you run the script multiple times, the following keys are expected to be
different: 'getloadavg', 'getpid', 'getpgrp', 'getsid', 'fd.'... (especially
the st_ino field).
"""

import errno  # pylint: disable=unused-import
import os
import socket
import stat
import sys


if getattr({}, 'iteritems', None):

  def iteritems(d):
    return d.iteritems()
else:  # Python 3.

  def iteritems(d):
    return d.items()


def stat2type(st):
  """Converts a stat struct to a string describing the file type."""
  mode = st.st_mode
  if stat.S_ISREG(mode):
    return 'reg'
  if stat.S_ISDIR(mode):
    return 'dir'
  if stat.S_ISBLK(mode):
    return 'blk'
  if stat.S_ISCHR(mode):
    return 'chr'
  if stat.S_ISFIFO(mode):
    return 'fifo'
  if stat.S_ISLNK(mode):
    return 'lnk'
  if stat.S_ISSOCK(mode):
    return 'sock'


def fix_exc_as(s):
  if sys.version_info[:2] < (3,):
    # Python 2.4 needs `,' instead of `as'.
    return s.replace(' as e:\n', ', e:\n')
  else:
    # Python 3 needs `as' instead of `,'.
    return s


# pylint: disable=exec-used
populate_or_exc_ary = []
exec(fix_exc_as(r'''
def populate_or_exc(d, k, vf):
  try:
    d[k] = vf()
  except Exception as e:
    d[k] = e
populate_or_exc_ary.append(populate_or_exc)'''))
populate_or_exc = populate_or_exc_ary.pop()


get_fd_info_ary = []
exec(fix_exc_as(r'''
def get_fd_info(fd):
  try:
    st = os.fstat(fd)
  except OSError as e:
    if e.args[0] != errno.EBADF:  # There was a file decriptor for listdir.
      raise
    return None
  try:
    ttyname = os.ttyname(fd)
  except OSError as e:
    if e.args[0] != errno.ENOTTY:
      raise
    ttyname = None
  return stat2type(st), ttyname, st
get_fd_info_ary.append(get_fd_info)'''))
get_fd_info = get_fd_info_ary.pop()


def get_python_info(wsgi_env=None):
  """Returns an info dict about the active Python environment."""
  # TODO(pts): Add info from /proc/self/maps.
  d = {}
  populate_or_exc(d, 'getsid', lambda: os.getsid(os.getpid()))
  for k in ('getpid', 'getppid', 'getresuid', 'getresgid', 'getgroups',
            'getcwd', 'getlogin', 'getloadavg', 'getpgrp', 'uname'):
    populate_or_exc(d, k, getattr(os, k, None))
  if getattr(os, 'getresuid', None) is None:  # Python2.4.
    populate_or_exc(d, 'getresuid', lambda: (os.getuid(), os.geteuid(), None))
  if getattr(os, 'getresgid', None) is None:  # Python2.4.
    populate_or_exc(d, 'getresgid', lambda: (os.getgid(), os.getegid(), None))
  for k in ('gethostname',):
    populate_or_exc(d, k, getattr(socket, k, None))
  for k in ('stdin', 'stdout', 'stderr'):
    populate_or_exc(d, k, lambda: getattr(sys, k).fileno())
  populate_or_exc(d, 'fds', lambda: list(map(int, os.listdir('/proc/self/fd'))))
  if isinstance(d['fds'], (list, tuple)):
    fds = d['fds']
  else:
    fds = ()
  for fd in fds:
    k = 'fd.%d' % fd
    populate_or_exc(d, k, lambda fd=fd: get_fd_info(fd))
    if d[k] is None:
      del d[k]
  # Python 2.7 and Python 3.4 attributes are mixed in here.
  for k in ('_multiarch', 'argv', 'api_version', 'byteorder', 'exec_prefix',
            'executable', 'flags', 'float_info', 'float_repr_style',
            'hexversion', 'long_info', 'meta_path', 'path', 'path_hooks',
            'platform', 'prefix', 'pydebug', 'version', 'version_info',
            'warnoptions', '_home', 'abiflags', 'base_exec_prefix',
            'base_prefix', 'dont_write_bytecode', 'hash_info', 'int_info',
            'implementation', 'thread_info'):
    populate_or_exc(d, k, lambda: getattr(sys, k))
  for m, v in sorted(iteritems(sys.modules)):
    populate_or_exc(d, 'module.%s' % m,
                    lambda v=v: getattr(v, '__file__', None))
  for n, v in sorted(iteritems(os.environ)):
    d['env.%s' % n] = v
  if wsgi_env:
    for n, v in sorted(iteritems(wsgi_env)):
      d['wsgi.%s' % n] = v
  return d


def format_python_info(d):
  # The output is not directly parsable (it's the output of repr).
  output = ['python_info = {\n']
  for k, v in sorted(iteritems(d)):
    output.append('  %r: %r,\n' % (k, v))
  output.append('}\n')
  return ''.join(output)


def get_python_info_str(wsgi_env=None):
  d_ary = ['python_info = error\n']
  exec(fix_exc_as(r'''if 1:
  try:
    d_ary[0] = format_python_info(get_python_info(wsgi_env))
  except Exception as e:
    d_ary[0] = 'python_info = %r\n' % e'''))
  return d_ary[0]


def application(env, start_response):
  """WSGI application entry point. For uWSGI and Gunicorn.

  Usage: uwsgi_python --http-socket :3399 --need-app --module python_info
  Usage: gunicorn --bind :3399 python_info

  Then visit: http://127.0.0.1:3399/
  """
  start_response('200 OK', [('Content-Type','text/plain')])
  return (get_python_info_str(env),)


def main(argv):  # pylint: disable=unused-argument
  """Usable from the command-line or as a CGI-script."""
  sys.stdout.write('Content-Type: text/plain\n\n')
  sys.stdout.write(get_python_info_str())
  sys.stdout.flush()


if __name__ == '__main__':
  sys.exit(main(sys.argv))
