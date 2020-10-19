"""

Scenario:
  Simulation of several iot devices (sensors) needing to receive calculated data
  from their connected server.
  If the calculation is heavy the server needs to send a request to a supercomputer
  which will handle the computation.

"""
import random

import simpy


RANDOM_SEED = 42     # Not so random but we want it reproducible
NUM_MACHINES = 1     # Number of calc machines.
NUM_SERVERS = 2      # Number of servers that are connected to sensors
CALC_TIME = 5        # Time it takes to calculate 
HEAVY_TIME = 10      # Time it takes for a heavy calculation
HEAVY_INTERVAL = 20  # How often a heavy calculation will be needed.
SIM_TIME = 400       # Simulation time in minutes

class Datacenter(object):
    """A datacenter with limited number of rented machines.

    Servers can request one of the machines (1 default). When they get one
    the calculation can start. It takes calctime minutes.
    """
    def __init__(self, env, num_machines, calctime):
        self.env = env
        self.machine = simpy.PriorityResource(env, num_machines)
        self.calctime = calctime

    def calc(self, val):
        """The calculation processes. It takes a ``val`` processes and tries
        to calculate it."""
        yield self.env.timeout(self.calctime)

class Serverfarm(object):
    """A server which several iot devices can request data from.
       However if the calculation is deemed too heavy then the server
       needs to ask for a fast machine in the data center to do the
       calculation.
    """
    def __init__(self, env, num_servers, calctime, datacenter):
        self.env = env
        self.server = simpy.PriorityResource(env, num_servers)
        self.calctime = calctime
        self.datacenter = datacenter

    def proc(self, val):
        """Processing the data incoming from a IOT device.
        """
        yield self.env.timeout(self.calctime)


def device(env, name, serverfarm):
    """The device process (each device has a ``name``) sends a request for data
    from (``server``).

    It then starts the calculation process and waits for it to finish...

    """
    print('%s sending request at %.2f.' % (name, env.now))
    with serverfarm.server.request() as request:
        yield request

        print('%s gets processed at %.2f.' % (name, env.now))
        yield env.process(serverfarm.proc(name))

        print('%s receives answer at %.2f.' % (name, env.now))

def setup(env, num_machines, num_servers, calctime, heavytime, t_inter):
    """Create a datacenter, a number of servers, a number of initial device requests and keep creating cars
    approx. every ``t_inter`` minutes."""
    # Create the datacenter
    datacenter = Datacenter(env, num_machines, heavytime)

    # Create the serverfarm
    serverfarm = Serverfarm(env, num_servers, calctime, datacenter)

    # Create 4 initial iot data requests
    for i in range(4):
        env.process(device(env, 'IOT %d' % i, serverfarm))

    # Create more iot data requests while the simulation is running
    while True:
        yield env.timeout(random.randint(t_inter - 2, t_inter + 2))
        i += 1
        env.process(device(env, 'IOT %d' % i, serverfarm))

# Setup and start the simulation
print('IOT Network simulation')

random.seed(RANDOM_SEED)  # This helps reproducing the results

# Create an environment and start the setup process
env = simpy.Environment()
env.process(setup(env, NUM_MACHINES, NUM_SERVERS, CALC_TIME, HEAVY_TIME, HEAVY_INTERVAL))

# Execute!
env.run(until=SIM_TIME)