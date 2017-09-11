import collections

from termcolor import cprint
from past.builtins import basestring

from . import config, formatting


def list_workflows(args):
    from . import config
    from termcolor import colored, cprint

    cfg = config.get()

    for workflow_location in cfg.workflow_dirs:

        print('Workflow location: %s' % formatting.pretty_path(workflow_location))
        for metafile in workflow_location.glob('*/metadata.yml'):
            meta = config.WorkflowMetadata(metafile)
            if not meta.matches(args.keywords):
                continue
            cprint(' - {name} ({version}): {description}'.format(
                    name=colored(meta.metadata['name'], 'green'),
                    description=meta.metadata['description'],
                    version=colored(meta.version, 'red')))
        print('')


def print_metadata(args):
    wflowdata = config.get_metadata_by_name(args.workflow_name,
                                            inspect_workflow=True)
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
        if key == 'name':
            writedata['Version'] = wflowdata.version

    for key, value in wflowdata.metadata.items():
        if key not in written:
            writedata[key] = value

    ss = formatting.yml_dump_color(writedata)
    cprint(ss)
    return


WRITEORDER = ['name', 'inputs', 'outputs', 'description', 'workflow_authors',
              'method_authors', 'methods', 'citations']

