import pickle

import pytest
import moldesign

import molflow
from molflow.convert import translate_cli_input
from molflow.utils import strtypes

from .helpers import pdbfile_path, twofile_path


def test_explicit_smiles_type():
    result = translate_cli_input('smi:c1ccccc1', 'pdb')
    mol = moldesign.read(pickle.loads(result), format='pdb')
    assert mol.num_atoms == 12


def test_type_from_file_extension():
    result = translate_cli_input(str(pdbfile_path), 'mmcif')
    mol = moldesign.read(pickle.loads(result), format='mmcif')
    assert mol.num_atoms == 1912


@pytest.mark.parametrize('inp,totype,expected',
                         [('3', 'int', 3),
                          ('3.0', 'float', 3.0),
                          ('3', 'number', 3),
                          ('3.0', 'number', 3.0),
                          ('3.0j', 'number', 3.0j),
                          (str(twofile_path), 'int', 2)])
def test_builtin_type_translation(inp, totype, expected):
    result = translate_cli_input(inp, totype)
    obj = pickle.loads(result)
    assert obj == expected
    if type(expected) in strtypes:
        assert type(obj) in strtypes
    else:
        assert type(obj) is type(expected)


def test_path_to_content_to_molecule_translation():
    inp = str(pdbfile_path)
    totype = 'str'
    expected = pdbfile_path.open('r').read()
    test_builtin_type_translation(inp, totype, expected)
