# Main code

import pdb

import openmdao.api as om

import numpy as np

np.set_printoptions(precision=10)

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


class PowerSplitter(om.ExplicitComponent):
    def setup(self):
        self.add_input('P_out', val=0.0, units='W')
        self.add_output('P_fuelcell', val=0.0, units='W')
        self.add_output('P_battery', val=0.0, units='W')

    def setup_partials(self):
        self.declare_partials('P_fuelcell', 'P_out')
        self.declare_partials('P_battery', 'P_out')

    def compute(self, inputs, outputs):
        P_out = inputs['P_out']
        x = 0.7
        # Split power between fuel cell and battery
        outputs['P_fuelcell'] = x * P_out  # 70% from fuel cell
        outputs['P_battery'] = (1 - x) * P_out  # 30% from battery

    def compute_partials(self, partials):
        x = 0.7
        partials['P_fuelcell', 'P_out'] = x
        partials['P_battery', 'P_out'] = 1 - x


class FuelCell(om.ExplicitComponent):
    def setup(self):
        self.add_input('P_fc', val=0.0, units='W')
        self.add_output('P_fuelcell', val=0.0, units='W')

    def setup_partials(self):
        self.declare_partials('P_fuelcell', 'P_fc')

    def compute(self, inputs, outputs):
        P_fc = inputs['P_fc']
        # Calculate P_fuelcell
        outputs['P_fuelcell'] = P_fc  # Modify this as needed

    def compute_partials(self, partials):
        partials['P_fuelcell', 'P_fc'] = 1.0


class Battery(om.ExplicitComponent):
    def setup(self):
        self.add_input('P_batt', val=0.0, units='W')
        #self.add_input('E_capacity_batt', val=30*3600, units='J') # 1 Wh = 3600 J
        self.add_input('E_capacity_batt', units='J') # 1 Wh = 3600 J
        self.add_input('SoC_initial')
        # 0.25C means 60min/0.25 (4h), 0.5C means 60min/0.5 (2h), 1C means 60 min,
        # 2C means 60min/2, 5C means 60min/5
        self.add_input('C_rate_batt') # 1C
        self.add_input('time', units='s') # 1 s
        self.add_output('E_final_batt', val=0.0, units='J')
        self.add_output('SoC_final', val=0.0)
        self.add_output('E_in_battery', val=0.0, units ='J')

    def setup_partials(self):
        #self.declare_partials('E_final_batt', 'P_batt')
        #self.declare_partials('SoC_final', 'P_batt')
        #self.declare_partials('E_in_battery', 'P_batt')
        self.declare_partials('E_final_batt', ['P_batt', 'E_capacity_batt', 'SoC_initial', 'time', 'C_rate_batt'])
        self.declare_partials('SoC_final', ['P_batt', 'E_capacity_batt', 'SoC_initial', 'time', 'C_rate_batt'])
        self.declare_partials('E_in_battery', ['P_batt', 'E_capacity_batt', 'SoC_initial', 'time', 'C_rate_batt'])

        # Shouldn't there be with respect to all *?

    def compute(self, inputs, outputs):
        P_batt = inputs['P_batt']
        E_capacity_batt = inputs['E_capacity_batt']
        SoC_initial = inputs['SoC_initial']
        time = inputs['time']
        C_rate_batt = inputs['C_rate_batt']

        max_power_allowed = (E_capacity_batt * SoC_initial * C_rate_batt) / (60 * 60) # [J]*[~]*[~]/[s]
        tolerance = 1e-14  # or whatever small value you consider appropriate
        if P_batt > max_power_allowed + tolerance:
        #if P_batt > max_power_allowed:
            #pdb.set_trace()  # Execution will stop here
            #print(f'P_batt: {P_batt}, E_capacity_batt: {E_capacity_batt}, max_power_allowed: {max_power_allowed}, SoC_initial: {SoC_initial}, time: {time}, C_rate_batt: {C_rate_batt}')
            #print(f'P_batt: {[f"{num:.14f}" for num in P_batt]}, E_capacity_batt: {[f"{num:.14f}" for num in E_capacity_batt]}, max_power_allowed: {[f"{num:.14f}" for num in max_power_allowed]}, SoC_initial: {[f"{num:.14f}" for num in SoC_initial]}, time: {[f"{num:.14f}" for num in time]}, C_rate_batt: {[f"{num:.14f}" for num in C_rate_batt]}')
            raise ValueError('Battery power exceeds maximum power allowed by C-rate')
        # Calculate the final energy in the battery
        outputs['E_final_batt'] = (E_capacity_batt * SoC_initial) - (P_batt * time)
        # Calculate change in SoC for the particular time step which is 1 [s]
        delta_SoC = ((P_batt * time) - E_capacity_batt) / E_capacity_batt
        # Calculate final SoC
        # If P_batt is + ve, then delta_SoC is - ve, else delta_SoC is + ve, which means SoC increases.
        outputs['SoC_final'] = SoC_initial + delta_SoC
        outputs['E_in_battery'] = E_capacity_batt

    def compute_partials(self, inputs, partials):
        P_batt = inputs['P_batt']
        E_capacity_batt = inputs['E_capacity_batt']
        SoC_initial = inputs['SoC_initial']
        time = inputs['time']

        partials['E_final_batt', 'P_batt'] = -1 * time
        partials['E_final_batt', 'E_capacity_batt'] = SoC_initial
        partials['E_final_batt', 'SoC_initial'] = E_capacity_batt
        partials['E_final_batt', 'time'] = -1 * P_batt
        partials['E_final_batt', 'C_rate_batt'] = 0  # C_rate_batt does not affect E_final_batt directly

        partials['SoC_final', 'P_batt'] = time / E_capacity_batt
        partials['SoC_final', 'E_capacity_batt'] = -1 * (P_batt * time) / (E_capacity_batt ** 2)
        partials['SoC_final', 'SoC_initial'] = 1
        partials['SoC_final', 'time'] = P_batt / E_capacity_batt
        partials['SoC_final', 'C_rate_batt'] = 0  # C_rate_batt does not affect SoC_final directly

        partials['E_in_battery', 'E_capacity_batt'] = 1
        partials['E_in_battery', 'P_batt'] = 0  # P_batt does not affect E_in_battery directly
        partials['E_in_battery', 'SoC_initial'] = 0  # SoC_initial does not affect E_in_battery directly
        partials['E_in_battery', 'time'] = 0  # time does not affect E_in_battery directly
        partials['E_in_battery', 'C_rate_batt'] = 0  # C_rate_batt does not affect E_in_battery directly


class TotalMass(om.ExplicitComponent):
    def setup(self):
        self.add_input('P_fuelcell', val=0.0, units='W')
        self.add_input('E_battery', val=0.0, units='J')
        self.add_input('fuelcell_power_density', val=1000, units='W/kg')  # W/kg
        self.add_input('battery_energy_density', val=25*3600, units='J/kg')  # J/kg
        # 1C = 0.00027778 Ah
        self.add_input('C_rate_batt') #1C
        self.add_output('mass_total', val=0.0, units='kg')

    def setup_partials(self):
        self.declare_partials('mass_total', 'P_fuelcell')
        self.declare_partials('mass_total', 'E_battery')

    def compute(self, inputs, outputs):
        P_fuelcell = inputs['P_fuelcell']
        E_battery = inputs['E_battery']
        fuelcell_power_density = inputs['fuelcell_power_density']
        battery_energy_density = inputs['battery_energy_density']
        # Calculate fuel cell mass
        mass_fuelcell = P_fuelcell / fuelcell_power_density
        # Calculate battery mass
        mass_battery = E_battery / battery_energy_density
        # Total mass equals to fuel cell mass + battery mass
        outputs['mass_total'] = mass_fuelcell + mass_battery

    def compute_partials(self, inputs, partials):
        fuelcell_power_density = inputs['fuelcell_power_density']
        battery_energy_density = inputs['battery_energy_density']
        partials['mass_total', 'P_fuelcell'] = 1.0 / fuelcell_power_density
        partials['mass_total', 'E_battery'] = 1.0 / battery_energy_density

class Propulsion(om.Group):
    def setup(self):
        self.add_subsystem('motor', Motor(), promotes_inputs=['P_req_shaft'])

class Power(om.Group):
    def setup(self):
        self.add_subsystem('powersplitter', PowerSplitter())
        self.add_subsystem('fuelcell', FuelCell())
        self.add_subsystem('battery', Battery())
        # self.add_subsystem('con_power_total', om.ExecComp('P_total = P_fuelcell + P_batt'), promotes_inputs=['P_fuelcell', 'P_batt','P_total'])

class Mass(om.Group):
    def setup(self):
        self.add_subsystem('total_mass', TotalMass())

# Instantiate the top level model
prob = om.Problem()

# Create a new instance of IndepVarComp
ivc = om.IndepVarComp()

# Add an output to the IndepVarComp. This output acts as an independent variable in your model.
# prob.model.set_input_defaults('SoC_initial', 1.0)
ivc.add_output('SoC_initial', val=1.0)
# prob.model.set_input_defaults('P_req_shaft', 100.0)
ivc.add_output('P_req_shaft', val=100, units='W')
ivc.add_output('E_capacity_batt', val=30*3600, units='J') # 30 Wh
ivc.add_output('C_rate_batt', val=1) # 1C
ivc.add_output('fuelcell_power_density', val=1000, units='W/kg')
ivc.add_output('battery_energy_density', val=25*3600, units='J/kg')
ivc.add_output('time', val=1, units='s') # 1 s

# Add the IndepVarComp to your model
prob.model.add_subsystem('ivc', ivc, promotes=['*'])

# Add the groups to the top level model
prob.model.add_subsystem('propulsion', Propulsion())
prob.model.add_subsystem('power', Power())
prob.model.add_subsystem('mass', Mass())

# Connect the IVC.P_req_shaft with P_out in motor component under propulsion group
prob.model.connect('P_req_shaft', 'propulsion.P_req_shaft')

# Connect the output of the Motor to the input of the PowerSplitter
prob.model.connect('propulsion.motor.P_in', 'power.powersplitter.P_out')

# Connect the output of the PowerSplitter to the input of the FuelCell and Battery
prob.model.connect('power.powersplitter.P_fuelcell', 'power.fuelcell.P_fc')
prob.model.connect('power.powersplitter.P_battery', 'power.battery.P_batt')

# Connect the IVC.SoC_initial with SoC_initial in battery component under power group
prob.model.connect('SoC_initial', 'power.battery.SoC_initial')
# Connect the IVC.time with time in battery component under power group
prob.model.connect('time', 'power.battery.time')
# Connect the IVC.E_capacity_battery with E_capacity_battery in battery component under power group
prob.model.connect('E_capacity_batt', 'power.battery.E_capacity_batt')
# Connect the IVC.C_rate_batt with C_rate_batt in battery component under power group
prob.model.connect('C_rate_batt', 'power.battery.C_rate_batt')
prob.model.connect('C_rate_batt', 'mass.total_mass.C_rate_batt')

# Connect the output of the FuelCell and Battery to the input of the TotalMass
prob.model.connect('power.fuelcell.P_fuelcell', 'mass.total_mass.P_fuelcell')
prob.model.connect('power.battery.E_in_battery', 'mass.total_mass.E_battery')
# Connect the IVC.fuelcell_power_density with fuelcell_power_density in total_mass component under mass group
prob.model.connect('fuelcell_power_density', 'mass.total_mass.fuelcell_power_density')
# Connect the IVC.battery_energy_density with battery_energy_density in total_mass component under mass group
prob.model.connect('battery_energy_density', 'mass.total_mass.battery_energy_density')

# Define the design variables, objectives, and constraints
# prob.model.add_design_var('propulsion.motor.', lower=200.0, upper=1000.0)
prob.model.add_design_var('E_capacity_batt', lower=1*60*60, upper=100*60*60) # 1 to 60 Wh

prob.model.add_objective('mass.total_mass.mass_total')
prob.model.add_constraint('power.fuelcell.P_fuelcell', upper=400.0)

# Define the driver
prob.driver = om.ScipyOptimizeDriver()
prob.driver.options['optimizer'] = 'SLSQP'
prob.driver.options['maxiter'] = 1000  # Increase the maximum number of iterations
prob.driver.options['tol'] = 1e-6  # Adjust the tolerance

# Setup the problem
prob.setup()

# Set initial values for your inputs
#prob.set_val('propulsion.motor.P_out', 200.0)

# Run the model
prob.run_driver()

# Print the results
print(prob.get_val('mass.total_mass.mass_total'))