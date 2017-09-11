from __future__ import absolute_import

import yaml
from pathlib import Path
import pickle
from .config import configuration
from .utils import RMODE, WMODE
from .serializers import BUILTIN_TYPES

PICKLE_PROTOCOL = 2
CONVERTPOLLTIME = 2
MAXCONVERTCPU = 1


# TODO: remove redundancy between this and the actual `convert` workflow
RECOGNIZED = set('mdt pdb mmcif cif sdf mol2 xyz smi smiles inchi name pdbcode mol'.split())

__CONVERTER = None
def get_converter():
    if __CONVERTER is None:
        convert_config = configuration.get_workflow_by_name('convert', raise_issues=True)
        __CONVERTER = convert_config.workflow
    return __CONVERTER 


def drive_converter(args):
    from .runners.localrunner import LocalRunner

    user_input, infmt = load_argument(args.input)
    outpath = Path(args.output)
    outfmt = outpath.suffix.lstrip('.')

    if args.input_format:
        infmt = args.input_format

    if args.output_format:
        outfmt = args.output_format

    #if infmt is None:
    #    print('FAILURE: cannot infer format of "%s". '
    #          'Explicitly specify the input format with "--input-format"')
    #    sys.exit(10)

    inputs = {'input_data': pickle.dumps(user_input, protocol=PICKLE_PROTOCOL),
              'input_format': pickle.dumps(infmt, PICKLE_PROTOCOL),
              'output_format': pickle.dumps(outfmt, PICKLE_PROTOCOL)}

    runner = LocalRunner(get_converter(), inputs, MAXCONVERTCPU, CONVERTPOLLTIME)
    runner.run()
    result = runner.output_files['result']
    with outpath.open(WMODE) as outfile:  # TODO: handle python objects (don't deserialize them)
        outfile.write(pickle.loads(result.open('rb').read()))
    print('Wrote file to %s' % outpath)


def load_argument(s):
    """
    First draft of a typed argument handler.

    Arguments:
        s (str): input string from CLI

    Returns:
        Tuple[str, str]: tuple of (content, inferred file format (or None if not inferred)]

    TODO: handle user-specified types?
    TODO: handle compressed files transparently
    """
    path = Path(s)
    if path.is_file():
        return path.open('rb').read(), path.suffix.lstrip('.')
    else:
        fields = s.split(':')
        if len(fields) == 2:
            return fields[1], fields[0]
        else:
            assert len(fields) == 1
            return s, None  # just return the string


def get_help():
    formatpath = Path(__file__).parents[0] / 'static' / 'formats.yml'
    with formatpath.open('r') as ymlfile:
        formats = yaml.load(ymlfile)

    helpstrs = ['Supported formats:']
    for key, value in formats.items():
        if 'extensions' in value:
            exts = ', '.join(value['extensions'])
        else:
            exts = key
        helpstrs.append(' - %s: %s' % (exts, value['help']))
        if 'type' in value:
            helpstrs[-1] += ' (%s)' % value['type']

    return '\n'.join(helpstrs)


def translate_cli_input(clidata, desired):
    """ Prepare command line arguments to be used as inputs for workflows.

    This deals with the fact that everything from the command line is just a string, so we need to
    transform it into the appropriate types.

    Args:
        clidata (str): data from the command line arguments
        input_extension (str): file extension, if read from a file (None otherwise)
        desired (str): desired output type (from `molflow.convert.RECOGZNIED` or `BUILTIN_TYPES`)
    """
    from .runners.localrunner import LocalRunner

    input_extension = None

    fields = clidata.split(':')
    data = fields[-1]
    if len(fields) > 1:
        assert len(fields) == 2
        input_extension = fields[0]

    aspath = Path(data)
    if aspath.exists():
        print('Found file %s' % aspath)
        if input_extension is None:
            input_extension = aspath.suffix.lstrip('.')
        with aspath.open('rb') as infile:
            data = infile.read()

    # if it's a basic type, just parse it
    if desired in BUILTIN_TYPES:
        return pickle.dumps(BUILTIN_TYPES[desired](data), protocol=PICKLE_PROTOCOL)

    else:
        # TODO: shouldn't need to pickle the strings here
        inputs = {'input_data': pickle.dumps(data, protocol=PICKLE_PROTOCOL),
                  'input_format': pickle.dumps(input_extension, protocol=PICKLE_PROTOCOL),
                  'output_format': pickle.dumps(desired, protocol=PICKLE_PROTOCOL)}

        runner = LocalRunner(get_converter(), inputs, MAXCONVERTCPU, CONVERTPOLLTIME)
        runner.run()
        return runner.output_files['result'].open('rb').read()
