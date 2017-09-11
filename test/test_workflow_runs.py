from pathlib import Path

from molflow.__main__ import _runargs
from molflow.utils import RMODE, WMODE

from .helpers import pdbfile_path
import pytest


@pytest.mark.parametrize('instring,num_expected',
                         [(str(pdbfile_path), 1912),
                          ('CC=C', 9),
                          ('methane', 5),
                          ('smi:c1ccccc1', 12)])
def test_run_num_atoms(instring, num_expected, tmpdir):
    tmppath = Path(str(tmpdir))
    _runargs('run count_atoms %s -o %s' % (instring, tmppath))

    with (tmppath / 'numatoms.txt').open(RMODE) as infile:
        num_atoms = int(infile.read().strip())
    assert num_atoms == num_expected


def test_outputdir_backup(tmpdir):
    path = Path(str(tmpdir))
    resultpath = (path / 'result.txt')
    bakpath = (path / 'old.1')
    bak2path = (path / 'old.2')

    # first run creates outputs in tmpdir
    _runargs('run add_two_to_it 5 -o %s' % path)
    assert _filecontent(resultpath) == '7'

    # second run should create backup automatically
    _runargs('run add_two_to_it 6.0 -o %s --overwrite' % path)
    assert resultpath.exists()
    assert _filecontent(resultpath) == '8.0'
    assert bakpath.exists()
    assert _filecontent(bakpath / 'result.txt') == '7'
    assert not bak2path.exists()

    # third run moves last results to old.2
    _runargs('run add_two_to_it -3.0 -o %s --overwrite' % path)
    assert resultpath.exists()
    assert _filecontent(resultpath) == '-1.0'
    assert _filecontent(bakpath / 'result.txt') == '7'
    assert _filecontent(bak2path / 'result.txt') == '8.0'

def test_no_output_to_cwd_parents():
    cwd = Path('./').absolute()
    testdir = cwd.parents[0]

    with pytest.raises(IOError):
        _runargs('run add_two_to_it 5 -o %s' % testdir)

    with pytest.raises(IOError):
        _runargs('run add_two_to_it 5 -o %s --overwrite' % testdir)


def _filecontent(path):
    with path.open('r') as rfile:
        return rfile.read().strip()
