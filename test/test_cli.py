import subprocess
import io
from pathlib import Path
import pickle

import moldesign  # required for tests

from molflow.__main__ import _runargs
from molflow.loader import load_workflow
from molflow.utils import RMODE, WMODE

from .helpers import redirect_stdout, module_path, testpath
import pytest


def test_load_workflow_from_repo():
    workflow = load_workflow('convert')
    assert workflow.name == 'convert'


def test_load_workflow_from_path():
    workflow = load_workflow(testpath / 'test_workflow')
    assert workflow.name == 'test_workflow'


def test_info_cmd_from_runargs():
    buffer = io.BytesIO()
    with redirect_stdout(buffer):
        _runargs('info add_two_to_it')
    assert buffer.getvalue()


def test_list_works_from_cli():
    listing = subprocess.check_output('molflow list',
                                      shell=True,
                                      cwd=str(module_path))
    assert listing


def test_run_add_two_int_argument_runargs(tmpdir):
    tmppath = str(tmpdir)
    _runargs('run add_two_to_it 5 -o {tmpdir}'.format(tmpdir=tmppath))
    path = Path(tmppath)
    _assert_result(path, 7)


def test_run_add_two_int_argument_cli(tmpdir):
    tmppath = str(tmpdir)
    path = Path(tmppath)
    with (path / 'input.txt').open(WMODE) as inputfile:
        inputfile.write(str(7.0))
    subprocess.check_output('molflow run add_two_to_it input.txt',
                            shell=True,
                            cwd=tmppath)
    _assert_result(path, 9.0)


def _assert_result(path, val):
    with (path/'result.txt').open(RMODE) as infile:
        assert infile.read().strip() == str(val)
    with (path/'result.pkl').open('rb') as infile:
        assert pickle.load(infile) == val

