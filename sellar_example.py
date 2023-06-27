import openmdao.api as om
import numpy as np


class SellarDis1(om.ExplicitComponent):
    def setup(self):
        self.add_input('z', val=np.zeros(2))
        self.add_input('x', val=0.)
        self.add_input('y2', val=1.0)
        self.add_output('y1', val=1.0)
        self.declare_partials('*', '*', method='fd')

    def compute(self, inputs, outputs):
        z1 = inputs['z'][0]
        z2 = inputs['z'][1]
        x1 = inputs['x']
        y2 = inputs['y2']

        outputs['y1'] = z1**2 + z2 + x1 - 0.2*y2

class SellarDis2(om.ExplicitComponent):
    def setup(self):
        self.add_input('z', val=np.zeros(2))
        self.add_input('y1', val=1.0)
        self.add_output('y2', val=1.0)
        self.declare_partials('*', '*', method='fd')

    def compute(self, inputs, outputs):
        z1 = inputs['z'][0]
        z2 = inputs['z'][1]
        y1 = inputs['y1']

        outputs['y2'] = y1**.5 + z1 + z2

class SellarMDA(om.Group):
    def setup(self):
        cycle = self.add_subsystem('cycle', om.Group(), promotes=['*'])
        cycle.add_subsystem('d1', SellarDis1(), promotes_inputs=['x', 'z', 'y2'],
                            promotes_outputs=['y1'])
        cycle.add_subsystem('d2', SellarDis2(), promotes_inputs=['z', 'y1'],
                            promotes_outputs=['y2'])

        cycle.set_input_defaults('x', 1.0)
        cycle.set_input_defaults('z', np.array([5.0, 2.0]))

        self.add_subsystem('obj_cmp', om.ExecComp('obj = x**2 + z[1] + y1 + exp(-y2)',
                                                  z=np.array([0.0, 0.0]), x=0.0),
                           promotes=['x', 'z', 'y1', 'y2', 'obj'])

        self.add_subsystem('con_cmp1', om.ExecComp('con1 = 3.16 - y1'), promotes=['con1', 'y1'])
        self.add_subsystem('con_cmp2', om.ExecComp('con2 = y2 - 24.0'), promotes=['con2', 'y2'])


prob = om.Problem()
model = prob.model

model.add_subsystem('sellar_mda', SellarMDA())
prob.setup()

om.n2(prob, outfile="coupled_no_solver.html", display_in_notebook=False)
prob.run_model()
prob.model.list_outputs();