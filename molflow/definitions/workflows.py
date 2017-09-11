# Copyright 2016 Autodesk Inc.
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
from __future__ import print_function
from collections import OrderedDict

from . import datasources as data


class WorkflowDefinition(object):
    """ ``WorkflowDefinition`` objects are used to construct and store workflow specifications.

    A workflow describes the relationship between a series of tasks, specifically how outputs from
    tasks should be used as inputs for subsequent tasks.

    Note that Workflow objects only _describe_ the workflow. To _run_ a workflow, you will use a
    :class:`pyccc.workflow.WorkflowRunner`-derived class.

    Args:
        name (str): name of this workflow
        metadata (dict): metadata object with fields to classify
           this workflow (optional)
    """
    def __init__(self, name, metadata=None):
        self.name = name
        self.tasks = {}
        self.inputs = OrderedDict()
        self.outputs = OrderedDict()
        self.metadata = metadata
        self.definition_path = None

    def __repr__(self):
        try:
            return 'Workflow "%s": %d inputs, %d steps, %s outputs' % \
                   (self.name, len(self.inputs), self.num_steps, len(self.outputs))
        except:
            return "<WorkflowDefinition object at %s>" % id(self)

    @property
    def num_steps(self):
        return len(self._get_dag(False))

    def steps(self):
        return self._get_dag(False).keys()

    def functions(self):
        return set(step.fn for step in self.steps())

    def add_input(self, name, description=None, type=None, default=None):
        """ Create an input for this workflow.

        Args:
            name (str): name of the input; must be unique for this workflow.
            description (str): optional description of the input
            type (DataTypes): optional data type for this input
            default (object): optional default value if not provided

        Returns:
            ExternalInput: a reference to this input data
        """
        if name in self.inputs:
            raise ValueError('Cannot add input named "%s" to "%s" - ' % (name, self) +
                             'an input with this name already exists.')

        inputdata = data.ExternalInput(name, self, description, type, default)
        self.inputs[name] = inputdata
        return inputdata

    def set_output(self, source, name, description=None, type=None):
        """ Create an output for this workflow.

        Args:
            name (str): name of this output; must be unique for this workflow.
            source (TaskOutput): the source of this output
            description (str): optional description of this data
            type (DataTypes): optional data type for this data
        """
        if name in self.outputs:
            raise ValueError('Cannot add output named "%s" to "%s" - ' % (name, self) +
                             'an output with this name already exists.')

        self.outputs[name] = data.WorkflowOutput(name, self, source, description, type)

    def to_cwl(self):
        inputs = {key: 'File' for key in self.inputs}
        outputs = {key: {'outputSource': outputdata.source.to_cwl(), 'type': 'File'}
                   for key, outputdata in self.outputs.items()}
        steps = {step._label(): step.to_cwl() for step in self.steps()}

        cwldoc = {'class': 'Workflow',
                  'cwlVersion': 'v1.0',
                  'inputs': inputs,
                  'outputs': outputs,
                  'steps': steps}

        return cwldoc


    def check_inputs(self, inputs):
        errs = []

        # TODO: type checking
        provided_inputs = set(inputs.keys())
        expected_inputs = set(self.inputs.keys())

        if provided_inputs-expected_inputs:
            names = ', '.join('"%s"' % name for name in provided_inputs-expected_inputs)
            errs.append('The following inputs aren\'t recognized by this workflow: ' + names)
        if expected_inputs-provided_inputs:
            names = ', '.join('"%s"' % name for name in expected_inputs-provided_inputs)
            errs.append('These required inputs were missing: ' + names)

        if errs:
            raise IOError('\n'.join(errs))

    def _get_dag(self, with_data=False):
        """ Create dependency graph for all steps in the DAG of the form

        steps[step] = {dep1, dep2, ...}
        """
        # TODO: deal with function name collisions

        dependencies = {}
        def dive(step):
            if step in dependencies:
                return
            else:
                dependencies[step] = set()

            for arg in step.args:  # kwargs?
                if isinstance(arg, data.ExternalInput):
                    upstream = arg
                    candive = False
                elif hasattr(arg, 'step'):
                    candive = True
                    upstream = arg.step
                else:
                    continue  # not a step or input data so assume it's static data

                if upstream in dependencies[step]:
                    continue
                else:
                    dependencies[step].add(upstream)
                    if candive:
                        dive(arg.step)

        for outputdata in self.outputs.values():
            dive(outputdata.source.step)
            if with_data:
                dependencies[outputdata] = set([outputdata.source.step])

        return dependencies

    def _to_graphviz(self):
        from graphviz import Digraph
        graph = Digraph(repr(self), graph_attr={'fontsize': '10', 'size':'7'})
        steps = self._get_dag(with_data=True)

        for step in steps:
            graph.node(step._label(), shape='rectangle')
        for inputdata in self.inputs.values():
            graph.node(inputdata._label(), shape='oval', color='orange')
        for outputdata in self.outputs.values():
            graph.node(outputdata._label(), shape='oval', color='blue')

        for step, dependencies in steps.items():
            for dep in dependencies:
                graph.edge(dep._label(), step._label())
        return graph

    def draw(self):
        return self._to_graphviz()
