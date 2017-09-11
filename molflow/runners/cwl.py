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

from pathlib import Path
import shutil
import yaml

from ..run import EXECUTOR
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
