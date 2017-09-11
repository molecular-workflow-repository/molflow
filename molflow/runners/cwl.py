from pathlib import Path
import shutil
import yaml

from ..run import EXECUTOR
from ..loader import load_workflow


def export_cwl(args):
    workflow = load_workflow(args.workflow_name)
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
