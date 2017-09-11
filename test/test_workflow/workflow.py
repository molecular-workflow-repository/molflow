from molflow import definitions as df

wf = df.WorkflowDefinition('test_workflow')
__workflow__ = wf

a = wf.add_input('a', 'a number', type=int)
b = wf.add_input('b', 'another number', default=3, type=float)

add = df.Function(funcname='add', sourcefile='./functions.py')
divide = df.Function(funcname='divide', sourcefile='./functions.py')
to_float = df.Function(funcname='cast_to_float', sourcefile='./functions.py')

doubled_a = add(a, a)
doubled_float_b = to_float(add(b, b))
ratio = divide(b, a)

wf.set_output(ratio, 'ratio_b_to_a')
wf.set_output(doubled_float_b, 'doubled_float_b')
wf.set_output(doubled_a, 'doubled_int_a')
