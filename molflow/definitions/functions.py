from pathlib import Path

import yaml
from past.builtins import basestring

from .steps import Step

FILEARRAY = {'type': 'array', 'items': 'File'}
INTARRAY = {'type': 'array', 'items': 'int'}


class Function(object):
    """ A function in the DAG
    """
    def __init__(self, funcname, sourcefile=None, python_module=None,
                 num_args=None, num_returnvals=None, docker_image=None):
        if (sourcefile and python_module) or not (sourcefile or python_module):
            raise ValueError("Define *either* `sourcefile` or `python_module`, not both.")

        self._docker_image = docker_image
        self.sourcefile = Path(sourcefile)
        self.python_module = python_module
        self.funcname = funcname
        self.name = funcname
        self.execount = 0
        self.num_args = num_args
        self.num_returnvals = num_returnvals

    def __str__(self):
        if self.sourcefile:
            return "Workflow Function '%s' defined in '%s'" % (self.funcname, self.sourcefile)
        else:
            return 'Workflow Function "%s.%s"' % (self.python_module, self.funcname)

    def __repr__(self):
        return '<%s>' % self

    def __call__(self, *args):  # , **kwargs): -- kwargs disabled for now
        num_args = len(args)
        if self.num_args is None:
            self.num_args = num_args
        elif num_args != self.num_args:
            raise ValueError('Inconsistent number of arguments for %s' % self)

        num_returnvals = _expecting_args()
        if self.num_returnvals is None:
            self.num_returnvals = num_returnvals
        elif num_returnvals != self.num_returnvals:
            raise ValueError("Inconsistent number of return values for %s" % self)

        self.execount += 1
        step = Step(self, args, {}, execount=self.execount)

        if num_returnvals == 1:
            return step.get_result(0)
        else:
            return tuple(step.get_result(i) for i in range(num_returnvals))

    def get_docker_image(self, rootdir):
        if self._docker_image:
            return self._docker_image

        elif self.sourcefile:
            return _get_docker_image(Path(rootdir) / self.sourcefile)

        else:
            raise ValueError('No docker image specified for this function')

    def to_cwl_tool(self, workflowdir):
        base_command = ['python']

        if self.python_module:
            funcname = self.python_module + '.' + self.funcname
        else:
            funcname = self.funcname

        arguments = ['--numreturn', str(self.num_returnvals), funcname]
        if self.python_module:
            arguments.extend(['--pymodule', self.python_module])
        inputs = self._get_input_cwl()
        requirements = [{'class': 'DockerRequirement',
                         'dockerPull': self.get_docker_image(workflowdir)}]

        outputs = {'return.%d.pkl' % i:
                       {'type': "File", 'outputBinding': {'glob': 'return.%d.*' % i}}
                   for i in range(self.num_returnvals)}

        cwldoc = {'class': 'CommandLineTool',
                  'cwlVersion': 'v1.0',
                  'baseCommand': base_command,
                  'inputs': inputs,
                  'arguments': arguments,
                  'requirements': requirements,
                  'outputs': outputs}

        return cwldoc

    def _get_input_cwl(self):
        inputs = {'runstep.py': {'type': 'File',
                                 'inputBinding': {'position': -2},
                                 'default': {'class': 'File', 'location': './runstep.py'}}}
        if self.sourcefile:
            inputs[self.sourcefile.name] = {'type': 'File',
                                            'inputBinding': {'prefix': '--sourcefile',
                                                             'position': -1},
                                            'default': {'class': 'File',
                                                        'location': './' + self.sourcefile.name}}
        for i in range(self.num_args):
            inputs['arg_%d' % i] = {'type': 'File',
                                    'inputBinding': {'position': i+4}}

        return inputs

    def write_cwl(self, sourcedir, dest):
        with (dest / self.name).with_suffix('.cwl').open('w') as cwlfile:
            yaml.safe_dump(self.to_cwl_tool(sourcedir), cwlfile, allow_unicode=True)


class ExternalWorkflow(Function):
    def __init__(self, name, version):
        self.name = name
        self.version = version
        self.execount = 0


def _get_docker_image(sourcefile):
    """ Not great! But I like the alternatives even less
    """
    with Path(sourcefile).open('r') as sf:
        for line in sf:
            fields = line.split('=')
            if len(fields) == 2 and fields[0].strip() == '__DOCKER_IMAGE__':
                return eval(fields[1].strip())
        else:
            return None


def _expecting_args():
    """Return how many values the caller is expecting.
    From
    https://code.activestate.com/recipes/284742-finding-out-the-number-of-values-the-caller-is-exp/
    """
    import sys, dis

    if sys.version_info.major == 2:
        get_ord = ord
    else:
        get_ord = lambda x: x

    f = sys._getframe().f_back.f_back
    i = f.f_lasti + 3
    bytecode = f.f_code.co_code
    instruction = get_ord(bytecode[i])
    while True:
        if instruction == dis.opmap['DUP_TOP']:
            if get_ord(bytecode[i + 1]) == dis.opmap['UNPACK_SEQUENCE']:
                return get_ord(bytecode[i + 2])
            i += 4
            instruction = get_ord(bytecode[i])
            continue
        if instruction == dis.opmap['STORE_NAME']:
            return 1
        if instruction == dis.opmap['UNPACK_SEQUENCE']:
            return get_ord(bytecode[i + 1])
        return 1  #amvmod - always return at least 1
