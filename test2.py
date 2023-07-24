# Main code

import openmdao.api as om

class Motor(om.ExplicitComponent):
    def setup(self):
        self.add_input('P_req_shaft', val=0.0, units='W')
        self.add_output('P_in', val=0.0, units='W')

    def setup_partials(self):
        self.declare_partials('P_in', 'P_req_shaft')

    def compute(self, inputs, outputs):
        P_req_shaft = inputs['P_req_shaft']
        motor_efficiency = 1
        outputs['P_in'] = P_req_shaft / motor_efficiency

    def compute_partials(self, partials):
        motor_efficiency = 1
        partials['P_in', 'P_req_shaft'] = 1.0 / motor_efficiency


class PowerSplit(om.ExplicitComponent):
    def setup(self):
        self.add_input('P_out', val=0.0, units='W')
        self.add_output('P_fuelcell', val=0.0, units='W')
        self.add_output('P_battery', val=0.0, units='W')

    def setup_partials(self):
        self.declare_partials('P_fuelcell', 'P_out')
        self.declare_partials('P_battery', 'P_out')

    def compute(self, inputs, outputs):
        P_out = inputs['P_out']
        # Split power between fuel cell and battery
        outputs['P_fuelcell'] = 0.7 * P_out  # 70% to fuel cell
        outputs['P_battery'] = 0.3 * P_out  # 30% to battery

    def compute_partials(self, partials):
        partials['P_fuelcell', 'P_out'] = 0.7
        partials['P_battery', 'P_out'] = 0.3

class FuelCell(om.ExplicitComponent):
    def setup(self):
        self.add_input('P_fc', val=0.0, units='W')
        self.add_output('P_fuelcell', val=0.0, units='W')

    def setup_partials(self):
        self.declare_partials('P_fuelcell', 'P_out')

    def compute(self, inputs, outputs):
        P_fc = inputs['P_fc']
        # Calculate P_fuelcell
        outputs['P_fuelcell'] = P_fc  # Modify this as needed

    def compute_partials(self, partials):
        partials['P_fuelcell', 'P_fc'] = 1.0

class Battery(om.ExplicitComponent):
    def setup(self):
        self.add_input('P_batt', val=0.0, units='W')
        self.add_input('E_capacity_batt', val=360000, units='J') # 1 Wh = 3600 J
        self.add_input('SOC_initial', val=0.8)
        # 0.25C means 60min/0.25 (4h), 0.5C means 60min/0.5 (2h), 1C means 60 min, 2C means 60min/2, 5C means 60min/5
        #self.add_input('C_rate_batt', val=60*60/2, units='s') #2C
        self.add_input('C_rate', val=1) # 1C
        self.add_input('time', val=1, units='s') # 1 s

        self.add_output('E_final_batt', val=0.0, units='J')

    def setup_partials(self):
        self.declare_partials('P_batt', 'E_battery')

    def compute(self, inputs, outputs):
        P_batt = inputs['P_batt']
        E_initial_batt = inputs['E_initial_batt']
        E_final_batt = inputs['E_final_batt']
        time = inputs['time']
        C_rate = inputs['C_rate']

        max_power = C_rate * E_initial_batt  # Maximum power allowed by C-rate 3600[J]/(60*60[s]/1)
        max_power = E_initial_batt * (C_rate/60*60) # Maximum power allowed by C-rate 3600[J]/(60*60[s]/C_rate)

        if P_batt > max_power:
            raise ValueError('Battery power exceeds maximum power allowed by C-rate')

        # Calculate the final energy in the battery
        outputs['E_batt_final'] = E_batt_initial - (P_batt * time)

    def compute(self, inputs, outputs):
        P_batt = inputs['P_batt']
        C_rate_batt = inputs['C_rate_batt']
        E_batt_initial = inputs['E_batt_initial']

        outputs['E_batt_final'] = E_batt_initial - (P_batt * C_rate_batt) #[J]-[J/s]/[s]

    def compute_partials(self, partials):
        partials['E_battery', 'P_batt'] = 1.0

class Battery(om.ExplicitComponent):
    def setup(self):
        self.add_input('P_batt', val=0.0, units='W')
        self.add_output('E_battery', val=0.0, units='W')
        self.add_output('SOC', val=0.0)  # State of Charge

        self.C_rate = 1.0  # C-rate
        self.capacity = 100.0  # Battery capacity in Wh
        self.SOC_initial = 0.8  # Initial state of charge

    def setup_partials(self):
        self.declare_partials('P_batt', 'E_batt')

    def compute(self, inputs, outputs):
        P_batt = inputs['P_batt']
        max_power = self.C_rate * self.capacity  # Maximum power allowed by C-rate

        if P_batt > max_power:
            raise ValueError('Battery power exceeds maximum power allowed by C-rate')

        # Calculate P_battery_out
        outputs['E_battery'] = P_batt * self.C_rate_batt   # Modify this as needed

        # Calculate state of charge
        outputs['SOC'] = self.SOC_initial - P_batt / self.capacity

    def compute_partials(self, partials):
        partials['P_battery', 'P_out'] = 1.0







class TotalMass(om.ExplicitComponent):
    def setup(self):
        self.add_input('P_fuelcell', val=0.0, units='W')
        self.add_input('P_battery', val=0.0, units='W')
        self.add_input('E_battery', val=0.0, units='J')
        self.add_input('fuelcell_power_density', val=1000, units='W/kg')  # W/kg
        self.add_input('battery_energy_density', val=25*3600, units='J/kg')  # J/kg
        # 1C = 0.00027778 Ah
        self.add_input('C_rate_batt', val=5)
        # 1C means 60 min, 2C means 60min/2, 5C means 60min/5
        # 0.5C means 60min/0.5 (2h). 0.25C means 60min/0.25 (4h), 0.125C means 60min/0.125 (8h)


        self.add_output('mass_total', val=0.0, units='kg')

    def setup_partials(self):
        self.declare_partials('mass_total', 'P_fuelcell')
        self.declare_partials('mass_total', 'E_battery')

    def compute(self, inputs, outputs):
        P_fuelcell = inputs['P_fuelcell']
        E_battery = inputs['E_battery']
        E_battery = inputs['E_battery']
        C_rate_batt = inputs['C_rate_batt']
        fuelcell_power_density = inputs['fuelcell_power_density']
        battery_energy_density = inputs['battery_energy_density']
        # Calculate fuel cell mass
        mass_fuelcell = P_fuelcell / fuelcell_power_density
        # Calculate battery mass
        mass_battery = E_battery / battery_energy_density
        # Total mass equals to fuel cell mass + battery mass
        outputs['mass_total'] = mass_fuelcell + mass_battery

    def compute_partials(self, inputs partials):
        fuelcell_power_density = 1000  # W/kg
        battery_energy_density = 250*3600  # J/kg (1/3600 = Wh/kg)
        partials['mass_total', 'P_fuelcell'] = 1.0 / fuelcell_power_density
        partials['mass_total', 'E_battery'] = 1.0 / battery_energy_density

class Propulsion(om.Group):
    def setup(self):
        self.add_subsystem('motor', Motor(), promotes_inputs=['P_req_shaft'])

class Power(om.Group):
    def setup(self):
        self.add_subsystem('powersplit', PowerSplit())
        self.add_subsystem('fuelcell', FuelCell())
        self.add_subsystem('battery', Battery())
        # self.add_subsystem('con_power_total', om.ExecComp('P_total = P_fuelcell + P_batt'), promotes_inputs=['P_fuelcell', 'P_batt','P_total'])

class Mass(om.Group):
    def setup(self):
        self.add_subsystem('total_mass', TotalMass())

# Instantiate the top level model
prob = om.Problem()

# Add the groups to the top level model
prob.model.add_subsystem('propulsion', Propulsion())
prob.model.add_subsystem('power', Power())
prob.model.add_subsystem('mass', Mass())

# Connect the output of the Motor to the input of the PowerSplit
prob.model.connect('propulsion.motor.P_in', 'power.powersplit.P_out')

# Connect the output of the PowerSplit to the input of the FuelCell and Battery
prob.model.connect('power.powersplit.P_fuelcell', 'power.fuelcell.P_fc')
prob.model.connect('power.powersplit.P_battery', 'power.battery.P_batt')

# Connect the output of the FuelCell and Battery to the input of the TotalMass
prob.model.connect('power.fuelcell.P_fuelcell', 'mass.total_mass.P_fuelcell')
prob.model.connect('power.battery.E_battery', 'mass.total_mass.E_battery')

# Connect the output of the Motor to the input of the constraint of the Total Power
#prob.model.connect('power.con_power_total.P_out', 'propulsion.motor.P_out')

# Define the driver
prob.driver = om.ScipyOptimizeDriver()
prob.driver.options['optimizer'] = 'SLSQP'
prob.driver.options['maxiter'] = 1000  # Increase the maximum number of iterations
prob.driver.options['tol'] = 1e-6  # Adjust the tolerance

# Define the design variables, objectives, and constraints

prob.model.set_input_defaults('P_req_shaft', 200.0)
prob.model.add_design_var('propulsion.motor.', lower=200.0, upper=1000.0)

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
