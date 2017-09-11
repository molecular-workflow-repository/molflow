import json
import yaml


def to_number(number):
    """ For arbitrary numeric values. Returns, by preference: int, float, or complex, if possible.
    """
    try:
        return int(number)
    except ValueError:
        pass

    try:
        return float(number)
    except ValueError:
        pass

    try:
        return complex(number)
    except ValueError:
        raise ValueError('Could not convert "%s" to any known numeric type' % number)


def _no_op(x):
    return x


def native_to_yaml(x):
    return yaml.dump(x.to_json())


SERIALIZERS = {'json': json.dumps,
               'yaml': yaml.dump,
               'str': _no_op,
               'units': native_to_yaml}

EXTENSIONS = {'units': 'yaml',
              'str': 'txt'}

for t in 'int float complex number'.split():
    SERIALIZERS[t] = str
    EXTENSIONS[t] = 'txt'

# TODO: physical units
BUILTIN_TYPES = {'str': str,
                 'int': int,
                 'float': float,
                 'number': to_number}



