# TODO: JMS 9/10: This isn't a runner, should be top level. Possible rename to cwl_command.py?

from pathlib import Path
import shutil
import yaml

from ..run import EXECUTOR
#from ..loader import load_workflow
from ..config import configuration


def export_cwl(args):
    workflow_config = configuration.get_workflow_by_name( args.workflow_name )
    workflow = workflow_config.workflow
    if args.outputdir is None:
        dest = Path('%s.cwl' % workflow.name)
    else:
        dest = Path(args.outputdir)

    workflow_to_cwl(workflow, dest)
    print('Exported workflow "%s" as CWL to: %s' % (workflow.name, dest))


def workflow_to_cwl(workflow, cwldirectory):
    path = Path(cwldirectory)

    if not path.exists():
        path.mkdir()

    shutil.copy(EXECUTOR, str(path/'runstep.py'))
    for function in workflow.functions():
        function.write_cwl(workflow.definition_path, path)
        if function.sourcefile:
            shutil.copy(str(workflow.definition_path/function.sourcefile),
                        str(path / function.sourcefile))

    with (path / 'workflow.cwl').open('w') as workflowfile:
        yaml.safe_dump(workflow.to_cwl(), workflowfile, allow_unicode=True)
