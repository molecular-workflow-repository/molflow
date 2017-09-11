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

import pickle


class ExternalInput(object):
    """ Placeholder for external (i.e., user) input
    """
    def __init__(self, name, workflow, description=None,
                 type=None, default=None):
        self.name = name
        self.description = description
        self.type = type
        self.workflow = workflow
        self.default = default

    def __repr__(self):
        return '<External input "%s">' % self.name

    def __str__(self):
        return 'Workflow input "%s"' % self.name

    def _label(self):
        return 'INPUT\n"%s"' % self.name

    def to_cwl(self):
        return self.name


class WorkflowOutput(object):
    """ Placeholder for a worfklow's output field
    """
    def __init__(self, name, workflow, source, description=None, type=None):
        self.name = name
        self.workflow = workflow
        self.source = source
        self.help = help
        self.type = type
        self.description = description

    def __str__(self):
        return 'Workflow output "%s"' % self.name

    def _label(self):
        return 'OUTPUT\n"%s"' % self.name

