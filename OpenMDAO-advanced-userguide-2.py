import openmdao.api as om
import numpy as np

class Resistor(om.ExplicitComponent):
    """
    Calculates the current across a resistor using Ohm's law.

    This component takes in two voltage inputs, 'V_in' and 'V_out', and calculates the current 'I' based on the voltage difference, and the value of the resistor 'R'. 
    
    The calculation is done using the formula I = (V_in - V_out) / R.

    Attributes (This means defined within the class, but then they are Public and are accessible outside class as well. Private has __R)
    ----------
    R : float
        The value of the resistor in ohms.

    Inputs
    ------
    V_in : float
        The input voltage in volts.
    V_out : float
        The output voltage in volts.

    Outputs
    -------
    I : float
        The current in amperes.
    """
    
    def initialize(self):
        self.options.declare('R', default=1.0, desc='Resistor')
        
    def setup(self):
        self.add_input('V_in', units='V')
        self.add_input('V_out', units='V')
        self.add_output('I', units='A')
        
    def setup_partials(self):
        self.declare_partials('I', 'V_in', method='fd')
        self.declare_partials('I', 'V_out', method='fd')
        
    def compute(self, inputs, outputs):
        R = self.options['R']
        deltaV = inputs['V_in']-inputs['V_out']
        outputs['I'] = deltaV/R

class Diode(om.ExplicitComponent):
    """
    Calculates the current across a diode using Shockley diode equation.
    -------------------------------------------------------------------

    This component takes in two voltage inputs, 'V_in' and 'V_out', and calculates the current 'I' based on the voltage difference, saturation current 'Is', and thermal voltage 'Vt'. 
    
    The calculation is done using the formula I = Is * [exp((V_in - V_out)/Vt) - 1].

    Attributes
    ----------
    Is : float
        Saturation current, in Amps.
    Vt : float
        Thermal voltage, in Volts.

    Inputs
    ------
    V_in : float
        The input voltage in volts.
    V_out : float
        The output voltage in volts.

    Outputs
    -------
    I : float
        The current in amperes.
    """
    
    def initialize(self):
        self.options.declare('Is', default=1e-15, desc='Saturation current, in A')
        self.options.declare('Vt', default=0.025875, desc='Thermal voltage, in V')
    
    def setup(self):
        self.add_input('V_in', units='V')
        self.add_input('V_out', units='V')
        self.add_output('I', units='A')
    
    def setup_partials(self):
        self.declare_partials('I', 'V_in', method='fd')
        self.declare_partials('I', 'V_out', method ='fd')
    
    def compute(self, inputs, outputs): 
        Is = self.options['Is']
        Vt = self.options['Vt']
        deltaV = inputs['V_in'] - inputs['V_out']
        outputs['I'] = Is * (np.exp(deltaV / Vt) - 1)
        
class Node(om.ImplicitComponent):
    """
    Calculates the voltage residual across a node based on incoming and the outgoing current.
    
    Attributes
    ----------
    n_in : int
        Number of incoming current connections.
    n_out : int
        Number of outgoing current connections.
    
    Inputs
    ------
    I_in:0, I_in:1, ..., I_in:n_in-1 : string
        Incoming currents (in Amps).
    I_out:0, I_out:1, ..., I_out:n_out-1 : string
        Outgoing currents (in Amps).
    
    Outputs
    -------
    V : float
        Voltage residual across the node (in Volts).
    """
    
    def initialize(self):
        self.options.declare('n_in', default=1, types=int, desc='number of incoming current connections')
        self.options.declare('n_out', default=1, types=int, desc='number of outgoing current connections')
    
    def setup(self):
        self.add_output('V', val=5.0, units='V')
        
        for i in range(self.options['n_in']):
            #Format Explanation - Takes in an int at 'i' in format(i), and this int 'i' is converted to string, and displayed in placeholder {} as 'I_in:3' for i = 3.
            i_name = 'I_in:{}'.format(i)
            self.add_input(i_name, units='A')
        
        for i in range(self.options['n_out']):
            i_name = 'I_out:{}'.format(i) 
            self.add_input(i_name, units='A')
            
    def setup_partials(self):
        """
        No partials with respect to 'V' are declared here because residual does not directly depend on it.
        """  
        
        self.declare_partials('V','I*', method='fd')
    
    def apply_nonlinear(self, inputs, outputs, residuals):
        residuals['V']=0.0
        
        for i_conn in range(self.options['n_in']):
            residuals['V'] += inputs['I_in:{}'.format(i_conn)]
            
        for i_conn in range(self.options['n_out']):
            residuals['V'] -= inputs['I_out:{}'.format(i_conn)]

import numpy as np

class Circuit(om.Group):

    def setup(self):
        self.add_subsystem('n1', Node(n_in=1, n_out=2), promotes_inputs=[('I_in:0', 'I_in')])
        self.add_subsystem('n2', Node())  # leaving defaults

        self.add_subsystem('R1', Resistor(R=100.), promotes_inputs=[('V_out', 'Vg')])
        self.add_subsystem('R2', Resistor(R=10000.))
        self.add_subsystem('D1', Diode(), promotes_inputs=[('V_out', 'Vg')])

        self.connect('n1.V', ['R1.V_in', 'R2.V_in'])
        self.connect('R1.I', 'n1.I_out:0')
        self.connect('R2.I', 'n1.I_out:1')

        self.connect('n2.V', ['R2.V_out', 'D1.V_in'])
        self.connect('R2.I', 'n2.I_in:0')
        self.connect('D1.I', 'n2.I_out:0')

        self.nonlinear_solver = om.NewtonSolver(solve_subsystems=False)
        self.nonlinear_solver.options['iprint'] = 2
        self.nonlinear_solver.options['maxiter'] = 20
        self.linear_solver = om.DirectSolver()
###############
#p = om.Problem()
#model = p.model

#model.add_subsystem('ground', om.IndepVarComp('V', 0., units='V'))
#model.add_subsystem('source', om.IndepVarComp('I', 0.1, units='A'))
#model.add_subsystem('circuit', Circuit())

#model.connect('source.I', 'circuit.I_in')
#model.connect('ground.V', 'circuit.Vg')

#p.setup()

# set some initial guesses
#p['circuit.n1.V'] = 10.
#p['circuit.n2.V'] = 1.

# sanity check: should sum to .1 Amps
#print(p['circuit.R1.I'] + p['circuit.D1.I'])

########

import openmdao.api as om
import numpy as np

p = om.Problem()
model = p.model

model.add_subsystem('ground', om.IndepVarComp('V', 0., units='V'))

# replacing the fixed current source with a BalanceComp to represent a fixed Voltage source
# model.add_subsystem('source', om.IndepVarComp('I', 0.1, units='A'))
model.add_subsystem('batt', om.IndepVarComp('V', 1.5, units='V'))
bal = model.add_subsystem('batt_balance', om.BalanceComp())
bal.add_balance('I', units='A', eq_units='V')

model.add_subsystem('circuit', Circuit())
model.add_subsystem('batt_deltaV', om.ExecComp('dV = V1 - V2', V1={'units':'V'},
                                               V2={'units':'V'}, dV={'units':'V'}))

# current into the circuit is now the output state from the batt_balance comp
model.connect('batt_balance.I', 'circuit.I_in')
model.connect('ground.V', ['circuit.Vg','batt_deltaV.V2'])
model.connect('circuit.n1.V', 'batt_deltaV.V1')

# set the lhs and rhs for the battery residual
model.connect('batt.V', 'batt_balance.rhs:I')
model.connect('batt_deltaV.dV', 'batt_balance.lhs:I')

p.setup()

###################
# Solver Setup
###################

# change the circuit solver to RunOnce because we're
# going to converge at the top level of the model with newton instead
p.model.circuit.nonlinear_solver = om.NonlinearRunOnce()
p.model.circuit.linear_solver = om.LinearRunOnce()

# Put Newton at the top so it can also converge the new BalanceComp residual
newton = p.model.nonlinear_solver = om.NewtonSolver()
p.model.linear_solver = om.DirectSolver()
newton.options['iprint'] = 2
newton.options['maxiter'] = 20
newton.options['solve_subsystems'] = True
newton.linesearch = om.ArmijoGoldsteinLS()
newton.linesearch.options['maxiter'] = 10
newton.linesearch.options['iprint'] = 2

# set initial guesses from the current source problem
p['circuit.n1.V'] = 9.8
p['circuit.n2.V'] = .7

p.run_model()

print(p['circuit.n1.V'])
print(p['circuit.n2.V'])
print(p['circuit.R1.I'])
print(p['circuit.R2.I'])
print(p['circuit.D1.I'])
