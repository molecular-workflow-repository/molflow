import sys
from pathlib import Path
import molflow


module_path = Path(molflow.__file__).parents[0]
testpath = Path(__file__).parents[0]
pdbfile_path = testpath / 'data' / '3AID.pdb'
twofile_path = testpath / 'data' / 'two.txt'

if sys.version_info.major == 3:
    from contextlib import redirect_stdout

else:
    assert sys.version_info.major == 2

    # copies directly from Python 3.5.3's contextlib
    class _RedirectStream(object):
        _stream = None
        def __init__(self, new_target):
            self._new_target = new_target
            # We use a list of old targets to make this CM re-entrant
            self._old_targets = []

        def __enter__(self):
            self._old_targets.append(getattr(sys, self._stream))
            setattr(sys, self._stream, self._new_target)
            return self._new_target

        def __exit__(self, exctype, excinst, exctb):
            setattr(sys, self._stream, self._old_targets.pop())


    class redirect_stdout(_RedirectStream):
        """Context manager for temporarily redirecting stdout to another file.
            # How to send help() to stderr
            with redirect_stdout(sys.stderr):
                help(dir)
            # How to write help() to a file
            with open('help.txt', 'w') as f:
                with redirect_stdout(f):
                    help(pow)
        """
        _stream = "stdout"