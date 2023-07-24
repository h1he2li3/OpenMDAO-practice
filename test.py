# Main code

# Last change - added `compute_partials` and `self.declare_partials` under setup
# `compute_partials` were added because `prob.check_totals` gave 0 in `J_fwd` or

import openmdao.api as om

class Motor(om.ExplicitComponent):
    def setup(self):
        self.add_input('P_out', val=0.0, units='W')
        self.add_output('P_in', val=0.0, units='W')

        self.declare_partials('P_in', 'P_out')

    def compute(self, inputs, outputs):
        P_out = inputs['P_out']
        efficiency = 1  # Motor efficiency

        # Calculate P_in_motor
        outputs['P_in'] = P_out / efficiency

    def compute_partials(self, inputs, partials):
        efficiency = 1  # Motor efficiency
        partials['P_in', 'P_out'] = 1.0 / efficiency

class FuelCell(om.ExplicitComponent):
    def setup(self):
        self.add_input('P_out', val=0.0, units='W')
        self.add_output('P_fuelcell', val=0.0, units='W')

        self.declare_partials('P_fuelcell', 'P_out')

    def compute(self, inputs, outputs):
        P_out = inputs['P_out']

        # Calculate P_fuelcell_out
        outputs['P_fuelcell'] = P_out  # Modify this as needed

    def compute_partials(self, inputs, partials):
        partials['P_fuelcell', 'P_out'] = 1.0

class TotalMass(om.ExplicitComponent):
    def setup(self):
        self.add_input('P_fuelcell', val=0.0, units='W')
        self.add_output('mass_total', val=0.0, units='kg')

        self.declare_partials('mass_total', 'P_fuelcell')

    def compute(self, inputs, outputs):
        P_fuelcell = inputs['P_fuelcell']
        power_density = 1.0  # kW/kg, modify this as needed

        # Calculate fuel cell mass
        mass_fuelcell = P_fuelcell / (power_density * 1e3)  # Convert kW to W

        # For now, total mass equals to fuel cell mass
        outputs['mass_total'] = mass_fuelcell

    def compute_partials(self, inputs, partials):
        P_fuelcell = inputs['P_fuelcell']
        power_density = 1.0  # kW/kg
        partials['mass_total', 'P_fuelcell'] = 1.0 / (power_density * 1e3)

class Propulsion(om.Group):
    def setup(self):
        self.add_subsystem('motor', Motor())

class Power(om.Group):
    def setup(self):
        self.add_subsystem('fuelcell', FuelCell())

class Mass(om.Group):
    def setup(self):
        self.add_subsystem('total_mass', TotalMass())

# Instantiate the top level model
prob = om.Problem()

# Add the groups to the top level model
prob.model.add_subsystem('propulsion', Propulsion())
prob.model.add_subsystem('power', Power())
prob.model.add_subsystem('mass', Mass())

# Connect the output of the Motor to the input of the FuelCell
prob.model.connect('propulsion.motor.P_in', 'power.fuelcell.P_out')

# Connect the output of the FuelCell to the input of the TotalMass
prob.model.connect('power.fuelcell.P_fuelcell', 'mass.total_mass.P_fuelcell')

# Define the driver
prob.driver = om.ScipyOptimizeDriver()
prob.driver.options['optimizer'] = 'SLSQP'
prob.driver.options['maxiter'] = 1000  # Increase the maximum number of iterations
prob.driver.options['tol'] = 1e-6  # Adjust the tolerance

# Define the design variables, objectives, and constraints
# lower bound on `propulsion.motor.P_out` must be greater than the input `propulsion.motor.P_out` or else the mass minimizes to the lower bound. If in doubt set, lower bound to lower value than `prob.set_val`
prob.model.add_design_var('propulsion.motor.P_out', lower=200.0, upper=1000.0)
prob.model.add_objective('mass.total_mass.mass_total')
prob.model.add_constraint('power.fuelcell.P_fuelcell', upper=400.0)

# Setup the problem
prob.setup()

# Set initial values for your inputs
prob.set_val('propulsion.motor.P_out', 200.0)

# Run the model
prob.run_driver()

# Print the results
print(prob.get_val('mass.total_mass.mass_total'))