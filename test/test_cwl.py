from pathlib import Path
import pickle
import subprocess

import pytest
from molflow.__main__ import _runargs


CWLFLAGS = "--tmpdir-prefix ./ --tmp-outdir-prefix ./ "


@pytest.fixture
def cwl_add_two(tmpdir):
    tmppath = Path(str(tmpdir))
    _runargs('writecwl add_two_to_it -o %s' % tmppath)
    return tmppath


def test_cwl_export_files(cwl_add_two):
    path = cwl_add_two
    assert (path / 'workflow.cwl').is_file()
    assert (path / 'functions.py').is_file()
    assert (path / 'add_one.cwl').is_file()
    assert (path / 'runstep.py').is_file()


def test_cwl_run(cwl_add_two):
    path = cwl_add_two
    resultfile = path / 'return.0.pkl'
    with (path / '__four.pkl').open('wb') as outfile:
        pickle.dump(4.0, outfile)

    assert not resultfile.exists()
    subprocess.check_call('cwltool %s workflow.cwl --number=__four.pkl' % CWLFLAGS,
                          cwd=str(path),
                          shell=True)

    assert resultfile.exists()
    with resultfile.open('rb') as infile:
        result = pickle.load(infile)

    assert result == 6.0












