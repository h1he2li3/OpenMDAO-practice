import numpy as np
import openmdao.api as om

SIZE = 10

p = om.Problem()

p.model.add_subsystem('arctan_yox', om.ExecComp('g=arctan(y/x)', has_diag_partials=True,
                                                g=np.ones(SIZE), x=np.ones(SIZE), y=np.ones(SIZE)),
                      promotes_inputs=['x', 'y'])

p.model.add_subsystem('circle', om.ExecComp('area=pi*r**2'), promotes_inputs=['r'])

p.model.add_subsystem('r_con', om.ExecComp('g=x**2 + y**2 - r', has_diag_partials=True,
                                           g=np.ones(SIZE), x=np.ones(SIZE), y=np.ones(SIZE)),
                      promotes_inputs=['r', 'x', 'y'])

thetas = np.linspace(0, np.pi/4, SIZE)
p.model.add_subsystem('theta_con', om.ExecComp('g = x - theta', has_diag_partials=True,
                                               g=np.ones(SIZE), x=np.ones(SIZE),
                                               theta=thetas))
p.model.add_subsystem('delta_theta_con', om.ExecComp('g = even - odd', has_diag_partials=True,
                                                     g=np.ones(SIZE//2), even=np.ones(SIZE//2),
                                                     odd=np.ones(SIZE//2)))

p.model.add_subsystem('l_conx', om.ExecComp('g=x-1', has_diag_partials=True, g=np.ones(SIZE), x=np.ones(SIZE)),
                      promotes_inputs=['x'])

IND = np.arange(SIZE, dtype=int)
ODD_IND = IND[1::2]  # all odd indices
EVEN_IND = IND[0::2]  # all even indices

p.model.connect('arctan_yox.g', 'theta_con.x')
p.model.connect('arctan_yox.g', 'delta_theta_con.even', src_indices=EVEN_IND)
p.model.connect('arctan_yox.g', 'delta_theta_con.odd', src_indices=ODD_IND)

p.driver = om.ScipyOptimizeDriver()
p.driver.options['optimizer'] = 'SLSQP'
p.driver.options['disp'] = False

# set up dynamic total coloring here
p.driver.declare_coloring()

p.model.add_design_var('x')
p.model.add_design_var('y')
p.model.add_design_var('r', lower=.5, upper=10)

# nonlinear constraints
p.model.add_constraint('r_con.g', equals=0)

p.model.add_constraint('theta_con.g', lower=-1e-5, upper=1e-5, indices=EVEN_IND)
p.model.add_constraint('delta_theta_con.g', lower=-1e-5, upper=1e-5)

# this constrains x[0] to be 1 (see definition of l_conx)
p.model.add_constraint('l_conx.g', equals=0, linear=False, indices=[0,])

# linear constraint
p.model.add_constraint('y', equals=0, indices=[0,], linear=True)

p.model.add_objective('circle.area', ref=-1)

p.setup(mode='fwd')

# the following were randomly generated using np.random.random(10)*2-1 to randomly
# disperse them within a unit circle centered at the origin.
p.set_val('x', np.array([ 0.55994437, -0.95923447,  0.21798656, -0.02158783,  0.62183717,
                          0.04007379,  0.46044942, -0.10129622,  0.27720413, -0.37107886]))
p.set_val('y', np.array([ 0.52577864,  0.30894559,  0.8420792 ,  0.35039912, -0.67290778,
                         -0.86236787, -0.97500023,  0.47739414,  0.51174103,  0.10052582]))
p.set_val('r', .7)

p.run_driver()

print(p['circle.area'])