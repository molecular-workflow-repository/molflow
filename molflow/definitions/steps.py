

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

