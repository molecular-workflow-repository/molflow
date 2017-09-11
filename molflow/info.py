import collections

from termcolor import cprint
from past.builtins import basestring

from . import config, formatting


def list_workflows(args):
    from . import config
    from termcolor import colored, cprint

    cfg = config.configuration

    for config_path in cfg.config_paths:
        workflows = cfg.get_local_workflows_by_config_path( config_path )
        if len(workflows) > 0:
            print('Workflow location: {}'.format(formatting.pretty_path(config_path)))
            for workflow in workflows:
                meta = workflow.metadata
                if not meta.matches(args.keywords):
                    continue
                cprint(' - {name} ({version}): {description}'.format(
                    name=colored(meta.metadata.get('name',workflow.name+' [Unnamed]'), 'green'),
                    description=meta.metadata.get('description','No Description'),
                    version=colored( workflow.versions.default_version()[0], 'red' ))) 
                if args.verbose:
                    cprint(workflow.versions.format_versions(offset=3))
            print('')


def print_metadata(args):
    cfg = config.configuration
    workflow_config = config.configuration.get_workflow_by_name( args.workflow_name )

    workflow = workflow_config.workflow  # This is important though unused, as having the actual workflow loads extra data about inputs and outputs into the metadata.    
    wflowdata = workflow_config.metadata

    writedata = collections.OrderedDict()
    written = set()
    for key in WRITEORDER:
        written.add(key)
        writekey = key.capitalize()
        if key in ('inputs', 'outputs'):
            writedata[writekey] = getattr(wflowdata, key, 'not provided')
        else:
            data = wflowdata.metadata.get(key, 'not provided')
            if isinstance(data, basestring):
                data = data.strip()
            writedata[writekey] = data
        # TODO: JMS 9/6: add this back in with versioning
        #       JMS 9/10: added in one way to use it, needs examination to see if it's ok.
        if key == 'name':
            writedata['Version'] = workflow_config.versions.default_version()[0]

    for key, value in wflowdata.metadata.items():
        if key not in written:
            writedata[key] = value

    ss = formatting.yml_dump_color(writedata)
    cprint(ss)
    return


WRITEORDER = ['name', 'inputs', 'outputs', 'description', 'workflow_authors',
              'method_authors', 'methods', 'citations']

