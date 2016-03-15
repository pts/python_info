python_info: script and library to display information about the active Python environment

Compatibility: Python >=2.4 (including Python 3.x).

The output is sorted (so its order is deterministic).

If you run the script multiple times, the following keys are expected to
have different values: 'getloadavg', 'getpid', 'getpgrp', 'getsid', 'fd.'...
(especially the st_ino field).

python_info is useful for debugging problems which happen on one system, but
not on another one: run python_info on both systems, look at diff, and
investigate from there.

Environments where python_info works:

* Direct invocation in the command-line.

* CGI script.

* Google App Engine handler.

* uWSGI application.

  $ sudo apt-get install uwsgi-plugin-python
  $ uwsgi_python --http-socket :3399 --need-app --module python_info

  Visit http://127.0.0.1:3399/

* Gunicorn application.

  $ sudo apt-get install gunicorn
  $ gunicorn --bind :3399 python_info

  Visit http://127.0.0.1:3399/
