# Copyright 2017 Autodesk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


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



