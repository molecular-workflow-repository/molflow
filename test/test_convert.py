from pathlib import Path
import pickle

import moldesign  # required for tests
from molflow.__main__ import _runargs
from molflow.utils import RMODE
from .helpers import pdbfile_path
import pytest


@pytest.mark.parametrize('suffix', 'mol2 sdf pdb xyz'.split())
def test_convert_smiles_to_structure(tmpdir, suffix):
    tmppath = Path(str(tmpdir))
    resultpath = tmppath / ('out.%s' % suffix)
    assert not resultpath.exists()
    _runargs('convert %s %s --fi smi' % ('c1ccccc1', resultpath))
    assert resultpath.exists()
    mol = moldesign.read(str(resultpath))
    assert mol.num_atoms == 12
    assert mol.num_residues == 1


def test_convert_pdb_to_mmcif(tmpdir):
    tmppath = Path(str(tmpdir))
    resultpath = tmppath/'out.mmcif'
    assert pdbfile_path.exists()
    assert not resultpath.exists()
    _runargs('convert %s %s'%(pdbfile_path, resultpath))
    assert resultpath.exists()

    mol = moldesign.read(str(resultpath))
    assert mol.num_atoms == 1912
    assert mol.num_residues == 207


def test_convert_pdb_to_parmed(tmpdir):
    import parmed
    tmppath = Path(str(tmpdir))
    resultpath = tmppath/'out.pkl'
    assert pdbfile_path.exists()
    assert not resultpath.exists()
    _runargs('convert %s %s --fo parmed' % (pdbfile_path, resultpath))
    assert resultpath.exists()

    with resultpath.open('rb') as pklfile:
        struc = pickle.load(pklfile)
    assert isinstance(struc, parmed.Structure)
    assert struc.num_atoms == 1912


CHEMIDS = [('smi', 'CC', 8),
           ('iupac', 'methane', 5),
           ('pdbcode', '1YU8', 600)]


@pytest.mark.parametrize('fmt,chemstring,natoms', CHEMIDS)
def test_autodetect_strings(tmpdir, chemstring, natoms, fmt):
    # Format is not used here (testing autodetection)
    tmppath = Path(str(tmpdir))
    resultpath = tmppath/'out.xyz'
    _run_string_conversion(natoms, resultpath, chemstring)


@pytest.mark.parametrize('fmt,chemstring,natoms', CHEMIDS)
def test_explicit_typed_strings(tmpdir, chemstring, natoms, fmt):
    # Format is not used here (testing autodetection)
    tmppath = Path(str(tmpdir))
    resultpath = tmppath/'out.xyz'
    instring = '%s:%s' % (fmt, chemstring)
    _run_string_conversion(natoms, resultpath, instring)


def _run_string_conversion(natoms, resultpath, s):
    assert not resultpath.exists()
    _runargs('convert %s %s' % (s, resultpath))
    assert resultpath.exists()
    with resultpath.open(RMODE) as xyzfile:
        n = int(xyzfile.readline().strip())
    assert n == natoms
