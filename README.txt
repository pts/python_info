python_info: script and library to display information about the active Python environment

Compatibility: Python >=2.4 (including Python 3.x).

The output is sorted (so its order is deterministic).

If you run the script multiple times, the following keys are expected to
have different values: 'getpid', 'getpgrp', 'getsid', 'fd.'... (especially
the st_ino field).
