import yaml
from pathlib import Path
from .config import get_workflow_dir


def load_workflow(wflow):
    """ Assemble and retreive workflow object from the specified directory

    TODO: load metadata as well

    Args:
        wflow (str or Path): name of workflow OR directory where the workflow resides

    Returns:
        molflow.definitions.WorkflowDefinition
    """
    dirpath = get_workflow_dir(wflow)
    workflow_path = dirpath / 'workflow.py'
    metadata_path = dirpath / 'metadata.yml'

    # execute the definition file
    namespace = {}
    with workflow_path.open("r") as wflowfile:
        code = compile(wflowfile.read(), "workflow.py", 'exec')
        exec(code, namespace)

    # load metadata only if available
    workflow = namespace['__workflow__']
    if metadata_path.exists():
        with metadata_path.open('r') as metafile:
            workflow.metadata = yaml.load(metafile)

    workflow.definition_path = dirpath
    return workflow
