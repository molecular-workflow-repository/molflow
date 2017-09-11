"""
This module determines and stores:
 - compute service configuration
 - workflow locations
"""
import collections
import pathlib
import yaml
from .versioning import Versions

from past.builtins import basestring

ConfigObj = collections.namedtuple('MolFlowConfig', ['workflow_dirs', 'versions'])

BUILTIN_WORKFLOWS = pathlib.Path(__file__).parents[1] / 'workflows'

_config_save = None


def get():
    """ Return the current configuration

    Returns:
        List[pathlib.Path]: list of *absolute paths* to directories to search for workflows
    """
    # TODO: user-specified workflow directories
    global _config_save

    if _config_save is None:
        workflow_dirs = [BUILTIN_WORKFLOWS.absolute()]
        versions = Versions()
        for dir in workflow_dirs:
            versions.read_version_hashes(dir)
        _config_save = ConfigObj(workflow_dirs=workflow_dirs,
                                 versions=versions)
    return _config_save


def get_workflow_dir(name):
    if isinstance(name, pathlib.Path) or '/' in name or '.' in name:  # it's a path
        wdir = pathlib.Path(name).absolute()
        if not wdir.is_dir():
            raise IOError('%s is neither a directory path nor a workflow name.' % wdir)
        else:
            return wdir

    else:
        for dir in get().workflow_dirs:
            wdir = dir.absolute()/name
            if wdir.is_dir():
                return wdir
        else:
            raise ValueError('No workflow named "%s" found in workflow search path.' % name)


def get_metadata_by_name(name, inspect_workflow=False):
    wdir = get_workflow_dir(name)
    metafile = wdir / 'metadata.yml'
    if metafile.is_file():
        data = WorkflowMetadata(metafile)
        if inspect_workflow:
            data.inspect_workflow()
        return data
    else:
        print("Warning: directory '%s' exists but has no metadata.yml")


class WorkflowMetadata(object):
    """
    Args:
        path (pathlib.Path): path to the file
    """
    def __init__(self, path):
        if path.exists():
            with path.open('r') as ymlfile:
                self.metadata = yaml.load(ymlfile)
        else:
            self.metadata = {}

        self.workflowdir = path.absolute().parents[0]
        self.sourcedir = self.workflowdir.parents[0]
        self._version = None
        self.inputs = []
        self.outputs = []

    @property
    def version(self):
        if self._version is None:
            self._version = get().versions.get_version_string(self.sourcedir, self.workflowdir.name)
        return self._version

    @property
    def last_version(self):
        versions = get().versions
        lastversion = versions.get_last_version(self.sourcedir, self.workflowdir.name)
        return lastversion

    def inspect_workflow(self):
        from .loader import load_workflow
        workflow = load_workflow(self.workflowdir)
        self.inputs = []
        self.outputs = []
        for key, val in workflow.inputs.items():
            self._format_item(key, val, self.inputs)

        for key, val in workflow.outputs.items():
            self._format_item(key, val, self.outputs)

    @staticmethod
    def _format_item(key, val, l):
        if val.description is None:
            val.description = ''
        inputstr = val.description.strip()
        if val.type.__class__ is type:
            inputstr = '(%s) ' % val.type.__name__+inputstr
        elif isinstance(val.type, basestring):
            inputstr = '(%s) ' % val.type+inputstr
        if getattr(val, 'default', None) is not None:
            inputstr += ' (default: %s)' % val.default
        l.append({key: inputstr.strip()})

    def update_version(self, newversion):
        versions = get().versions
        versions.update_version(self.sourcedir, self.workflowdir.name, newversion)

    def is_updated(self):
        versions = get().versions
        lastversion = self.last_version
        if lastversion == 'unversioned':
            return True
        elif lastversion.sha1 != versions.get_directory_sha1(self.workflowdir):
            return True
        else:
            return False

    def is_dirty(self):
        return get().versions.get_directory_dirty(self.workflowdir)

    def matches(self, keywords):
        for k in keywords:
            if k not in self.metadata.get('keywords', []):
                return False
        else:
            return True
