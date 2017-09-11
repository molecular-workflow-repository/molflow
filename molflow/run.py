from __future__ import print_function

import os

import yaml
from pathlib import Path
import pickle

from . import convert, formatting
from .serializers import SERIALIZERS, EXTENSIONS
from .loader import load_workflow
from .convert import translate_cli_input, CONVERTER

EXECUTOR = str(Path(__file__).parents[0]/'static'/'runstep.py')


def run_workflow(args):
    from .runners.localrunner import LocalRunner

    # Set up inputs and output destination
    workflow = load_workflow(args.workflow_name)
    inputs = get_inputs(workflow, args)
    outputpath = setup_output_dir(args.outputdir, workflow, args.overwrite)

    # Run it
    workflow.check_inputs(inputs)
    runner = LocalRunner(workflow, inputs, args.maxcpus, 2,
                         datadir=outputpath if args.saveall else None)
    runner.run()

    # Write outputs
    outputs = {key: f.open('rb').read() for key, f in runner.output_files.items()}
    write_outputs(outputpath, workflow, outputs)


def get_inputs(workflow, args):
    if len(args.inputs) != len(workflow.inputs):
        raise ValueError("Workflow %s expected %d inputs, but %d were passed"
                         % (workflow.name, len(workflow.inputs), len(args.inputs)))

    input_fields = {name: inputdata for name, inputdata in zip(workflow.inputs, args.inputs)}
    inputs = {}
    for name, spec in workflow.inputs.items():
        inputs[name] = translate_cli_input(input_fields[name], spec.type)
    return inputs


def setup_output_dir(dirpath, workflow, overwrite=False):
    cwd = Path('./').absolute()

    if dirpath is None:
        dirpath = Path('%s.run' % workflow.name)
    else:
        dirpath = Path(dirpath)

    abspath = dirpath.absolute()

    if abspath in cwd.parents:
        raise IOError("Molflow cannot write output to a parent of the current working directory")

    if cwd != abspath and dirpath.exists() and os.listdir(str(dirpath)):
        if not overwrite:
            formatting.fail(("Workflow output directory '%s' already exists. Specify a "
                            "different directory with '-o' or overwrite it with "
                             "'--overwrite'.") % dirpath)
        elif not dirpath.is_dir():
            formatting.fail(("Cannot overwrite '%s' - it exists, but is not a file. Specify a "
                            "different directory with '-o' or overwrite it with "
                             "'--overwrite'.") % dirpath)
        else:
            _backup_directory(dirpath)

    if not dirpath.exists():
        dirpath.mkdir()
    print('Output directory: %s' % dirpath.absolute())

    return dirpath


def _backup_directory(dirpath):
    backup_location = dirpath
    i = 0
    while backup_location.exists():
        i += 1
        backup_location = dirpath/('old.%d' % i)
    print("WARNING: moving contents of directory '%s' to '%s'" % (dirpath, backup_location))
    backup_location.mkdir()
    for p in dirpath.glob('*'):
        if p != backup_location and not p.name.startswith('old.'):
            p.rename(backup_location/p.name)


def write_outputs(outputpath, workflow, outputs):
    locations = {}
    for name, output in outputs.items():
        files = []

        picklepath = (outputpath/(name+'.pkl'))
        with picklepath.open('wb') as pklfile:
            pklfile.write(output)
        files.append(picklepath)

        spec = workflow.outputs[name]
        dtype = spec.type
        if dtype is None:
            dtype = 'object'
        elif type(dtype) is type:
            dtype = str(dtype.__name__)

        if dtype in SERIALIZERS:
            try:
                data = pickle.loads(output)
                serial = SERIALIZERS[dtype](data)
                ext = EXTENSIONS[dtype]
            except Exception as e:
                print('FAILED to convert output "%s" to type "%s": %s' %
                      (name, dtype, e))
                raise
            else:
                fpath = outputpath/(name+'.'+ext)
                with fpath.open('wb') as outfile:
                    outfile.write(serial)
                files.append(fpath)

        elif dtype in convert.RECOGNIZED:
            runner = run_local(CONVERTER, {'input_data': outfile,
                                           'input_format': 'object',
                                           'output_format': dtype})
            runner.run()
            data = runner.output_files['result']
            as_str = pickle.loads(data.read())
            with fpath.open('wb') as outfile:
                outfile.write(as_str)
            files.append(fpath)

        locations[name] = map(str, files)

    print(yaml.safe_dump({"Output locations": locations}, default_flow_style=False))