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

from ..run import EXECUTOR


def make_job(step, defdir, inputs, submit=False):
    job = _make_pyccc_job(step.fn, inputs, defdir)
    job.name = step._label()
    if submit:
        job.submit()
    return job


def _make_pyccc_job(fn, args, defdir, engine=None):
    import pyccc
    inputs = {'runstep.py': pyccc.files.LocalFile(str(EXECUTOR))}

    command = ['python runstep.py --numreturn %d' % fn.num_returnvals]
    if fn.sourcefile:
        command.append('--sourcefile %s' % fn.sourcefile.name)
        source_location = defdir/fn.sourcefile
        inputs[fn.sourcefile.name] = pyccc.files.LocalFile(str(source_location))
    elif fn.python_module:
        command.append('--pymodule %s' % fn.python_module)

    command.append(fn.funcname)
    for i, indata in enumerate(args):
        argfile = 'arg%d.pkl' % i
        inputs[argfile] = indata
        command.append(argfile)

    if engine is None:
        engine = pyccc.engines.Docker()

    job = pyccc.Job(engine=engine,
                    image=fn.get_docker_image(defdir),
                    command=' '.join(command),
                    inputs=inputs,
                    submit=False)
    return job
