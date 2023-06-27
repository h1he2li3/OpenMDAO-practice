import openmdao.api as om

# Splitting one ImplicitComponent into two explicit components


class SquareX(om.ExplicitComponent):
    def setup(self):
        self.add_input('x', val=1.0)
        self.add_output('y', val=1.0)
        self.declare_partials('y', 'x')

    def compute(self, inputs, outputs):
        x = inputs['x']
        outputs['y'] = x**2
        # Computing the First equation of y = x**2.

    def compute_partials(self, inputs, partials):
        partials['y', 'x'] = 2 * inputs['x']
        # Computing the first derivative of the First equation.


class TimesThreeY(om.ExplicitComponent):
    def setup(self):
        self.add_input('y', val=1.0)
        self.add_output('x', val=1.0)
        self.declare_partials('x', 'y', val=3.)

    def compute(self, inputs, outputs):
        y = inputs['y']
        outputs['x'] = 3.0*y
        # Computing the Second equation of x = 3y.

    # Why is there no compute_partials method?


p = om.Problem()
model = p.model

model.add_subsystem('square_x', SquareX())
model.add_subsystem('times_three_y', TimesThreeY())

model.connect('square_x.y', 'times_three_y.y')
# Connecting(A.y,B.y), WWhere 'y' variable value from 'ExplicitComponet A' is passed to 'y' variable in 'ExplicitComponent B'.
model.connect('times_three_y.x', 'square_x.x')
# Connecting(A.x,B.x), WWhere 'x' variable value from 'ExplicitComponet B' is passed to 'x' variable in 'ExplicitComponent A'.

model.nonlinear_solver = om.NewtonSolver(solve_subsystems=False)
model.linear_solver = om.DirectSolver()

p.setup()
p.run_model()
p.model.list_outputs()
