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

class Step(object):
    """ An execution of a function
    """
    def __init__(self, fn, args, kwargs, execount):
        self.fn = fn
        self.args = args
        #self.kwargs = kwargs
        self.fnexecount = execount

    def __str__(self):
        return "'%s' execution %d" % (self.fn.name, self.fnexecount)

    def __repr__(self):
        return "<%s>" % self

    def _label(self):
        return '%s.%d' % (self.fn.name, self.fnexecount)

    def get_result(self, position):
        return StepResult(self, position=position)

    def to_cwl(self):
        inputs = {'arg_%d' % i: arg.to_cwl() for i, arg in enumerate(self.args)}
        outputs = ['return.%d.pkl' % i for i in range(self.fn.num_returnvals)]

        return {'run': self.fn.name+'.cwl',
                'in': inputs,
                'out': outputs}



class StepResult(object):
    def __init__(self, step, position):
        self.step = step
        self.position = position

    def to_cwl(self):
        return '%s/return.%d.pkl' % (self.step._label(), self.position)

