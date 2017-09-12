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


"""
 config.py

 This module is used to handle the configuration of molflow. 
  It tracks: 
   - Information contained in the config file (~/.molflow/config) such as local repo paths
   - Configuration status of all discovered workflows (local or remote locations)
     - Workflow Definition
     - Workflow Metadata
     - Workflow Versions
  It is used by most command line functions in order to retrieve specific workflows, get information about them, run them, etc.
"""

from pathlib import Path                # All path operations. Note that we have
                                        # to workaround some things that are in
                                        # latest pathlib in Python 3.0 that
                                        # aren't implemented in the 2.7 pypi
                                        # version.

import yaml                             # Used for reading metadata.

from past.builtins import basestring    # Used for checking if something is str
                                        # or unicode. May no longer be needed if
                                        # we update the formatter. 

from termcolor import cprint, colored   # For colorizing warning/error
                                        # messages. Should not be needed if we
                                        # update the formatter to have a better
                                        # range of error messaging.
          

import configparser                     # Config file reader


from .versioning import WorkflowVersions  # Component of WorkflowConfig object.


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
    """
    def __init__(self, config_file_location = "~/.molflow/config"):
        """ Initializes a configuration object based on the path in which to find the configuration file. """
        config_file_path = Path(config_file_location)

        try:
            config_file_path = config_file_path.expanduser()
        except AttributeError:          # pathlib's 2.7 version doesn't have the
                                        # .expanduser function.
            import os.path
            config_file_path = Path(os.path.expanduser(config_file_location))
        
        try:
            self._configdata = self.load_config( config_file_path )
        except IOError:   # catching path not existing errors as well as others
                          # related to IO.
            self.create_config( config_file_path )
            self._configdata = self.load_config( config_file_path )

        self._config_paths = [Path(i) for i in self._configdata['Local Workflow Locations']['paths'].split('\n')]
                
        try:
            self._workflow_paths = [i.expanduser().absolute() for i in self._config_paths]
        except AttributeError:         # pathlib's 2.7 version doesn't have the
                                       # .expanduser function
            import os.path
            self._workflow_paths = [Path(os.path.expanduser(str(i))).absolute() for i in self._config_paths]
            
        # De-duplicate the list of config paths and workflow paths.  Note that
        # we have to do this on the expanded, absolute paths (e.g. the workflow
        # paths), but we also have to remove the config paths that caused
        # duplication, or we'll trigger some odd errors later when
        # get_config_path returns > 1 result. We remove duplicates arbitrarily.

        new_workflow_paths = []
        for i in self._workflow_paths:
            cp = self.get_config_path(i)
            if len(self.get_config_path(i)) > 1:
                self._config_paths.remove(cp[0])
            else:
                new_workflow_paths.append(i)
        self._workflow_paths = new_workflow_paths

        self.discover_local_workflows()
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
                if (workflow / 'workflow.py').exists() and (workflow / 'metadata.yml').exists():
                    wf = WorkflowConfiguration( name = workflow.stem,
                                                path = Path(workflow),
                                                config_path = self.get_config_path( workflow ))
                    self._all_local_workflows.append( wf )


        self._index_local_workflows()
    #end def discover_local_workflows( self, paths=None )

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

    # end def _index_local_workflows( self )

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
        """Determines which path in the configuration file was responsible for finding a workflow at the given path."""
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


#end class WorkflowConfig(object)


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
        self.inputs = []
        self.outputs = []

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

    def matches(self, keywords):
        for k in keywords:
            if k not in self.metadata.get('keywords', []):
                return False
        else:
            return True

#end class WorkflowMetadata(object)


# Important - this object is what typically gets used by all of the command
# options. We rarely need to create more than one Config, but it's occasionally
# useful if using this module interactively.

configuration = Config()
