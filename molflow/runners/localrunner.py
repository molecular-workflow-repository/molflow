import time
from pathlib import Path
import yaml
from ..definitions import datasources
from .localstep import make_job


class StepFailure(Exception):
    def __init__(self, msg, job):
        self.job = job
        self.msg = msg
        message = self._show_debugging_options()
        super(StepFailure, self).__init__(message)

    def _show_debugging_options(self):
        msg = [self.msg,
               "To launch a shell to examine the docker container, run:",
               "   docker commit %s mflw_debug_ \n" % self.job.jobid,
               "   docker run -it --entrypoint=bash mflw_debug_"]

        cmdfields = self.job.command.split()
        if cmdfields[0] == 'python':
            msg.extend([
               "Inside the docker container, you can run the PDB debugger with:",
               "   python -m pdb %s" % ' '.join(cmdfields[1:])
            ])

        return '\n'.join(msg)


class LocalRunner(object):
    def __init__(self, workflow, inputs, maxproc=4, polltime=4, datadir=None):
        self.workflow = workflow
        self.inputs = inputs
        self.maxproc = maxproc
        self.polltime = polltime
        if datadir is not None:
            datadir = Path(datadir)
        self.datadir = datadir

        self.queued = set(workflow.steps())
        self.running = {}
        self.finished = {}
        self.output_files = {}

    def run(self):
        print("\nStarting workflow '%s'" % self.workflow.name)
        self.workflow.check_inputs(self.inputs)

        if self.datadir and not self.datadir.exists():
            self.datadir.mkdir()

        changed = True
        try:
            while self.queued or self.running:
                if not changed:
                    time.sleep(self.polltime)
                changed = self.launch_jobs()
                changed = self.finish_jobs() or changed

        finally:  # clean up any running jobs
            for job in self.running.values():
                try:
                    if job.status.lower() not in ('finished', 'error'):
                        print('Killing %s - %s' % (job.name, job.jobid))
                        job.kill()
                except Exception as e:
                    print('Cleanup error: %s' % e)

        for key, outputdata in self.workflow.outputs.items():
            self.output_files[key] = _getdata(outputdata.source, self.finished)

        return self.output_files

    def launch_jobs(self):
        changed = False
        for step in list(self.queued):
            if len(self.running) >= self.maxproc:
                break
            readyinputs = []
            for arg in step.args:
                if isinstance(arg, datasources.ExternalInput):
                    readyinputs.append(self.inputs[arg.name])
                elif arg.step in self.finished:
                    readyinputs.append(_getdata(arg, self.finished))
                else:
                    readyinputs = None
                    break

            if readyinputs:
                self.queued.remove(step)
                changed = True
                job = make_job(step, self.workflow.definition_path, readyinputs, submit=True)
                print(yaml.safe_dump({job.name: {'engine': str(job.engine),
                                                 'image': job.image,
                                                 'job_id': job.jobid}},
                                     default_flow_style=False).rstrip(' \n'))

                self.running[step] = job
        return changed

    def finish_jobs(self):
        # TODO: check exit codes
        changed = False
        for step, job in list(self.running.items()):
            if job.status.lower() in ('finished', 'error'):
                failed = '__fail__.txt' in job.get_output()

                self.finished[step] = self.running.pop(step)
                changed = True

                if self.datadir:
                    stepdir = dump_job(self.datadir, job, step)
                    if not failed:
                        print('Step "%s" complete, outputs: %s\n' % (step._label(), stepdir))
                else:
                    if not failed:
                        print('Step "%s" complete.\n' % job.name)

                if failed:
                    print('\n     ------- STEP "%s" FAILED --------' % job.name)
                    print('STDERR from docker environment:')
                    raise StepFailure(job.stderr.strip())

        return changed


def dump_job(datadir, job, step):
    stepdir = datadir/step._label()
    if not stepdir.exists():
        stepdir.mkdir()
    for fname, oput in job.get_output().items():
        if '__pycache__' in fname or fname.endswith('.pyc'):
            continue
        else:
            path = (stepdir/Path(fname).name)
            oput.put(str(path))

    with (stepdir/'stdout').open('w') as stdoutfile:
        stdoutfile.write(job.stdout)
    with (stepdir/'stderr').open('w') as stderrfile:
        stderrfile.write(job.stderr)

    return stepdir


def _getdata(arg, finished):
    objname = 'return.%d.pkl' % arg.position
    txtname = 'return.%d.txt' % arg.position
    job = finished[arg.step]
    outputs = job.get_output()
    try:
        if txtname in outputs:
            outputfile = job.get_output(txtname)
        else:
            outputfile = job.get_output(objname)
    except KeyError:
        print('\n---- ERROR in workflow step %s ----\n'%arg.step._label()+
              'Expected output file "%s" not found.\n'%objname)
        info = {'name': job.name,
                'stdout': job.stdout,
                'stderr': job.stderr,
                'command': job.command,
                'jobid': job.jobid,
                'engine': str(job.engine),
                'input_files': list(job.inputs.keys()),
                'output_files': [filename for filename in job.get_output().keys()
                                 if '__pycache__' not in filename and not filename.endswith('.pyc')]}
        print(yaml.dump(info))
        raise IOError()
    else:
        return outputfile

