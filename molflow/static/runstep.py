#!/usr/bin/env python

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


""" Script that executes a workflow step in a docker container.
See documentation in `molflow/runners/README.md for explanation of CLI arguments.
"""
import argparse
import importlib
import os
import pickle
import sys

PICKLE_PROTOCOL = 2
PYTHONV = sys.version_info.major
assert PYTHONV in (2, 3)

if PYTHONV == 2:
    builtin = __builtins__


def parse_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('function')
    #parser.add_argument('--kwargs', nargs='*', default={})
    parser.add_argument('--unroll', nargs='+', default=[])
    parser.add_argument('--numreturn', type=int)
    parser.add_argument('--sourcefile', type=str)
    parser.add_argument('--pymodule', type=str)
    parser.add_argument('arguments', nargs=argparse.REMAINDER, default=[])
    #parser.add_argument('--literal', nargs='+', default=[])
    #parser.add_argument('--jsonfile', nargs='+', default=[])

    return parser.parse_args()


def get_arguments(cliargs):
    args = [load_argument(path) for path in cliargs.arguments]
    #clikwargs = {}
    #for arg in cliargs.kwargs:
    #    fields = arg.split('=')
    #    assert len(fields) == 2
    #    clikwargs[fields[0]] = fields[1]
    #kwargs = {key: load_argument(value) for key, value in clikwargs.items()}
    kwargs = {}

    return args, kwargs


def is_string(s):
    if PYTHONV == 2:
        return isinstance(s, basestring)
    else:
        return isinstance(s, str) or isinstance(s, bytes)


def get_function(cliargs):
    if cliargs.sourcefile:  # evaluate source code and import function
        namespace = {}
        with open(cliargs.sourcefile, 'r') as sourcefile:
            code = compile(sourcefile.read(), "cliargs.sourcefile", 'exec')
            exec(code, namespace)
        return namespace[cliargs.function]

    elif cliargs.pymodule:  # load from an importable module
        module = importlib.import_module(cliargs.pymodule)
        return getattr(module, cliargs.function)

    else:  # no module, assume built-in
        return getattr(builtin, cliargs.function)


def load_argument(path):
    if path.split('.')[-1].lower() in ('p', 'pkl', 'pickle'):
        with open(path, 'rb') as picklefile:
            data = pickle.load(picklefile)
        return data
    else:  # assume string TODO: py2 / py3 unicode issues
        with open(path, 'r') as infile:
            data = infile.read()
        return data


def serialize_output(returnval, cliargs):
    if cliargs.numreturn == 1:
        returnval = [returnval]

    for ival, outval in enumerate(returnval):
        if ival in cliargs.unroll:
            os.mkdir('return.%d' % ival)
            for iunroll, item in enumerate(outval):
                with open('return.%d/item%d.pkl' % (ival, iunroll), 'w') as outfile:
                    pickle.dump(item, outfile, protocol=PICKLE_PROTOCOL)

        #elif is_string(outval):
        #    with open('return.%d.txt' % ival, 'wb') as outfile:
        #        outfile.write(outval)

        else:
            with open('return.%d.pkl' % ival, 'wb') as outfile:
                pickle.dump(outval, outfile, protocol=PICKLE_PROTOCOL)


def main():
    try:
        cliargs = parse_cli()
        func = get_function(cliargs)
        args, kwargs = get_arguments(cliargs)
        returnval = func(*args, **kwargs)
        serialize_output(returnval, cliargs)
    except Exception as e:
        with open('__fail__.txt', 'w') as failfile:
            failfile.write(str(e))
        raise


if __name__ == '__main__':
    main()
