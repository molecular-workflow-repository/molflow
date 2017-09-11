# JMS 9/6/17 Needs updating
# """
# This module determines and stores:
#  - compute service configuration
#  - workflow locations
# """


#import collections

from pathlib import Path                # All path operations. Note that we have
                                        # to workaround some things that are in
                                        # latest pathlib in Python 3.0 that
                                        # aren't implemented in the 2.7 pypi
                                        # version.

import yaml                             # Used for reading metadata.

from past.builtins import basestring    # Used for checking if something is str
                                        # or unicode. May no longer be needed if
                                        # we update the formatter. JMS

from termcolor import cprint, colored

import configparser


from .versioning import WorkflowVersions


#ConfigObj = collections.namedtuple('MolFlowConfig', ['workflow_dirs', 'versions'])
#BUILTIN_WORKFLOWS = pathlib.Path(__file__).parents[1] / 'workflows'

# Configuration file used if none is found. 
sample_config_file = u"\
# Molflow configuration file.\n\
# For all locations, use separate lines for each path you want searched for workflows.\n\
[Local Workflow Locations]\n\
paths=~/.molflow/workflows/\n\
      ./\n\
\n\
[Remote Workflow Locations]\n\
github=https://github.com/molecular-workflow-repository/\n\
\n\
[User]\n\
# Currently Unused\n\
username=\n\
fullname=\n\
\n\
[Github]\n\
# Currently Unused\n\
anonymous=True\n\
user=\n\
pw=\n\
token=\n"

class Config( object ):
    """ 
    Config objects represent the configuration of the molflow workflow running system.
    They include the following key components:
       1. Information contained within the configuration file.
       2. State information for all local and remote workflows.
       3. 
    """
    def __init__(self, config_file_location = "~/.molflow/config"):
        """ Initializes a configuration object based on the path in which to find the configuration file. """
        config_file_path = Path(config_file_location)

        try:
            config_file_path = config_file_path.expanduser()
        except AttributeError:          # pathlib's 2.7 version doesn't have the .expanduser function.
            import os.path
            config_file_path = Path(os.path.expanduser(config_file_location))
        
        try:
            self._configdata = self.load_config( config_file_path )
        except IOError:   # catching path not existing errors as well as others related to IO.
            self.create_config( config_file_path )
            self._configdata = self.load_config( config_file_path )

        self._config_paths = [Path(i) for i in self._configdata['Local Workflow Locations']['paths'].split('\n')]
                
        try:
            self._workflow_paths = [i.expanduser().absolute() for i in self._config_paths]
        except AttributeError:         # pathlib's 2.7 version doesn't have the .expanduser function
            import os.path
            self._workflow_paths = [Path(os.path.expanduser(str(i))).absolute() for i in self._config_paths]

        self.discover_local_workflows()

        pass
    # end __init__(...)

    def load_config( self, config_file_path ):
        with config_file_path.open('rt') as f:
            config_parser = configparser.ConfigParser()
            config_parser.read_file( f )
        return config_parser
        

    def create_config( self, config_file_path ):
        print("Configuration file at {} not found, creating default config.".format( config_file_path ))
        config_dir = config_file_path.parent
        if not config_dir.exists():
            config_dir.mkdir(parents=True)   # equivalent to mkdir -p, so creates parents as needed
        elif not config_dir.is_dir():
            print("Could not create default config file: path's root {} exists and is a file, not a directory".format(config_dir))
            import sys
            sys.exit(1)

        with config_file_path.open("wt") as f:
            f.write( sample_config_file )

    def discover_local_workflows( self, paths=None ):
        if paths is None:
            paths = [p for p in self._workflow_paths if p.exists()]
            if len(paths) < len(self._workflow_paths):
                pass #print("Some of your local workflow paths defined in the config file did not exist.\n\
#Offending paths: {}".format([str(p) for p in self._workflow_paths if not p.exists()]))
        else:
            self._workflow_paths = paths

        self._all_local_workflows = []
        for p in paths:
            possible_workflows = [item for item in p.iterdir() if item.is_dir()]
            for workflow in possible_workflows:
                # TODO: JMS 9/10: Check if metadata is required or not. I would say it is.
                #                 Will change some later assumptions if it is not required.
                if (workflow / 'workflow.py').exists() and (workflow / 'metadata.yml').exists():
                    wf = WorkflowConfiguration( name = workflow.stem,
                                                path = Path(workflow),
                                                config_path = self.get_config_path( workflow ))
                    self._all_local_workflows.append( wf )


        self._index_local_workflows()

    def _index_local_workflows( self ):
        """ Builds some dictionaries so we can easily find workflows by name, path, config path. """
        
        self._workflows_by_name = {}
        self._workflows_by_config_path = {}

        for wf in self._all_local_workflows:
            # Index by name
            if wf.name in self._workflows_by_name:
                self._workflows_by_name[wf.name].append( wf )
            else:
                self._workflows_by_name[wf.name] = [wf]

            # Index by config path, note that there may be multiple
            # configuration paths that point to the same workflow. 
            # 
            # For example, if you ran molflow with the default config file and
            # ran from ~/.molflow/workflows, all workflows would show up twice
            # due to the './' entry and the '~/.molflow/workflows' entry.
            for config_path in wf.config_path:
                cp = str(config_path)
                if cp in self._workflows_by_config_path:
                    self._workflows_by_config_path[cp].append( wf )
                else:
                    self._workflows_by_config_path[cp] = [wf]

        # Check for duplicated names and warn.
        for wf_name in self._workflows_by_name.keys():
            if len( self._workflows_by_name[wf_name] ) > 1:
                print("A workflow named '{}' was found via multiple local workflow paths.\nLocations found: {}".format(wf_name, [i.config_path for i in self._workflows_by_name[wf_name]]))




        pass

    def get_local_workflows_by_config_path(self, config_path):
        return self._workflows_by_config_path.get(str(config_path),[])

    def get_local_workflows(self):
        return self._local_workflows


    def get_workflow_by_name( self, name , raise_issues=False ):
        # Note: currently hooked up to local only, needs to check both local and remotes eventually.
        try:
            workflows = self._workflows_by_name[name]
        except KeyError:
            cprint("{warning} {name} is not a valid workflow name.".format( 
                warning=colored("ERROR:",'red',attrs=['bold']),
                name=colored(name, 'green')))
            # TODO: JMS 9/10. Consider rebuilding the formatting module to be
            #                 useful and have a distinctive error formatter and
            #                 use that instead.
            import sys
            sys.exit(1)
        if raise_issues and len(workflows)>1:
            cprint("{warning} Multiple workflows found with name {name}:\n\
       {workflow_names}".format( 
                warning=colored("ERROR:",'red',attrs=['bold']),
                name=colored(name, 'green'),
                workflow_names=colored(str([str(i.path) for i in workflows]),'blue')))
            import sys
            sys.exit(1)

        return workflows[0]
            
    def get_config_path( self, path ):
        """Determines which workflow path in the configuration file was responsible for finding a workflow at the given path."""
        result = []
        if len(self._config_paths) == 0:
            return result
        try:
            self._config_paths[0].expanduser()
            expand = lambda x: x.expanduser().absolute()
        except AttributeError:
            import os.path
            expand = lambda x: Path(os.path.expanduser(str(x))).absolute()

        for p in self._config_paths:
            if expand(p) == path or expand(p) == path.parent:
                result.append(p)

        return result
        
    @property
    def config_paths( self ):
        return self._config_paths

class WorkflowConfiguration( object ):
    def __init__( self, name, path, config_path ):
        self.name = name
        self.path = path
        self.config_path = config_path
        self._metadata = None
        self._workflow = None
        self._versions = None

    @property
    def metadata( self ):
        if self._metadata is None:
            self._metadata = WorkflowMetadata( self.path / 'metadata.yml' )
        return self._metadata

    @property
    def workflow( self ):
        if self._workflow is None:
            # TODO: JMS Note: this section basically replaces loader.py
            namespace = {}
            workflow_path = self.path / 'workflow.py'
            with workflow_path.open("r") as wflowfile:
                code = compile(wflowfile.read(), "workflow.py", 'exec')
                exec(code, namespace)

            # load metadata only if available
            self._workflow = namespace['__workflow__']
            
            self.metadata.add_workflow_information( self._workflow )
            self._workflow.metadata = self.metadata.metadata
            self._workflow.definition_path = self.path
            
        return self._workflow

    @property
    def versions( self ):
        if self._versions is None:
            self._versions = WorkflowVersions( self.path )
        return self._versions

    def __repr__( self ):
        return "\
WorkflowConfiguration: Name: {self.name}\n\
                       Path: {self.path}\n\
                       ConfigPath: {self.config_path}".format( self=self )

    pass






configuration = Config()



# _config_save = None

# def get():
#     """ Return the current configuration
#
#     Returns:
#         List[pathlib.Path]: list of *absolute paths* to directories to search for workflows
#     """
#     # TODO: user-specified workflow directories
#     global _config_save
#
#     if _config_save is None:
#         workflow_dirs = [BUILTIN_WORKFLOWS.absolute()]
#         versions = Versions()
#         for dir in workflow_dirs:
#             versions.read_version_hashes(dir)
#         _config_save = ConfigObj(workflow_dirs=workflow_dirs,
#                                  versions=versions)
#     return _config_save


# def get_metadata_by_name(name, inspect_workflow=False):
#     wdir = get_workflow_dir(name)
#     metafile = wdir / 'metadata.yml'
#     if metafile.is_file():
#         data = WorkflowMetadata(metafile)
#         if inspect_workflow:
#             data.inspect_workflow()
#         return data
#     else:
#         print("Warning: directory '%s' exists but has no metadata.yml")



class WorkflowMetadata(object):
    """
    Args:
        path (pathlib.Path): path to the metadata file
    """
    def __init__(self, path):
        if path.exists():
            with path.open('r') as ymlfile:
                self.metadata = yaml.load(ymlfile)
        else:
            self.metadata = {}
        if self.metadata == None:
            self.metadata = {}
        #self.workflowdir = path.absolute().parents[0]
        #self.sourcedir = self.workflowdir.parents[0]
        # self._version = None
        self.inputs = []
        self.outputs = []

    # @property
    # def version(self):
    #     if self._version is None:
    #         self._version = get().versions.get_version_string(self.sourcedir, self.workflowdir.name)
    #     return self._version

    # @property
    # def last_version(self):
    #     versions = get().versions
    #     lastversion = versions.get_last_version(self.sourcedir, self.workflowdir.name)
    #     return lastversion

    def add_workflow_information(self, workflow):
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

    # def update_version(self, newversion):
    #     versions = get().versions
    #     versions.update_version(self.sourcedir, self.workflowdir.name, newversion)

    # def is_updated(self):
    #     versions = get().versions
    #     lastversion = self.last_version
    #     if lastversion == 'unversioned':
    #         return True
    #     elif lastversion.sha1 != versions.get_directory_sha1(self.workflowdir):
    #         return True
    #     else:
    #         return False

    # def is_dirty(self):
    #     return get().versions.get_directory_dirty(self.workflowdir)

    def matches(self, keywords):
        for k in keywords:
            if k not in self.metadata.get('keywords', []):
                return False
        else:
            return True
