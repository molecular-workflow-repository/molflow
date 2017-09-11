import sys

# deals with issues around pathlib.Path.open
if sys.version_info.major == 3:
    from contextlib import redirect_stdout
    RMODE = 'r'
    WMODE = 'w'
    strtypes = (str, bytes)
else:
    RMODE = 'rb'
    WMODE = 'wb'
    strtypes = (unicode, str, basestring)
