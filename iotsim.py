"""

Scenario:
  Simulation of several iot devices (sensors) needing to receive calculated data
  from their connected server.
  If the calculation is heavy the server needs to send a request to a supercomputer
  which will handle the computation.

"""
import random

import simpy

import matplotlib.pyplot as plt

# All times unless otherwise specified are in seconds

RANDOM_SEED = 42           # Not so random but we want it reproducible
NUM_MACHINES = 1           # Number of calc machines.
NUM_SERVERS = 2            # Number of gateway nodes that are connected to sensors
NUM_DEVICES = 10           # Number of edge devices
PROCESS_TIME = 1000        # Time it takes to calculate 
COMPUTE_TIME = 1000        # Time it takes for a heavy calculation
SEND_INTERVAL = 5000       # How often a edge device will send an image.
SIM_TIME = 4000000         # Simulation time in seconds

time_data = []          # List of dictionaries to store the data of how long a request takes.

class Datacenter(object):
    """
    A datacenter with limited number of rented machines A.K.A The cloud.

    Gateway nodes can request one of the machines (1 default). When they get one
    the calculation can start. It takes processtime seconds.
    """
    def __init__(self, env, num_machines, processtime):
        self.env = env
        self.machine = simpy.PriorityResource(env, num_machines)
        self.processtime = processtime

    def calc(self, val):
        """
        The calculation processes. It takes a ``val`` processes and tries
        to calculate it.
        """
        yield self.env.timeout(self.processtime)

class Serverfarm(object):
    """
    Our gateway devices, hopefully only one is needed.
    """
    def __init__(self, env, num_servers, processtime, datacenter):
        self.env = env
        self.server = simpy.PriorityResource(env, num_servers)
        self.processtime = processtime
        self.datacenter = datacenter

    def proc(self, val):
        """
        Processing the data incoming from a IOT device.
        """

        #Roughly 30% of all requests are heavy calculations.
        if random.randint(0,1) < 0.3:
            print("Process is heavy sending to data center!")
            yield env.process(self.datacenter.calc(val))
        else:
            print("Process light, handle at server.")
            yield self.env.timeout(self.processtime)


def device(env, name, serverfarm):
    """The device process (each device has a ``name``) sends a request for data
    from (``server``).

    It then starts the calculation process and waits for it to finish...

    """
    
    starttime = env.now
    with serverfarm.server.request() as request:
        yield request

        getsprocessed = env.now
        yield env.process(serverfarm.proc(name))

        getsanswered = env.now
        wt = getsprocessed - starttime
        pt = getsanswered - getsprocessed
        tt = getsanswered - starttime
        time_data.append({"waitTime": wt/1000, "processTime": pt/1000, "totalTime": tt/1000})

def setup(env, num_devices, num_machines, num_servers, processtime, computetime, t_inter):
    """Create a datacenter, a number of servers, a number of initial device requests and keep creating cars
    approx. every ``t_inter`` minutes."""
    # Create the datacenter
    datacenter = Datacenter(env, num_machines, computetime)

    # Create the serverfarm
    serverfarm = Serverfarm(env, num_servers, processtime, datacenter)

    # Create 4 initial iot data requests
    for i in range(4):
        env.process(device(env, 'IOT %d' % i, serverfarm))

    # Create more iot data requests while the simulation is running
    while True:
        yield env.timeout(t_inter/num_devices)
        i += 1
        env.process(device(env, 'IOT %d' % i, serverfarm))

# Setup and start the simulation
print('IOT Network simulation')

random.seed(RANDOM_SEED)  # This helps reproducing the results

# Create an environment and start the setup process
env = simpy.Environment()
env.process(setup(env, NUM_DEVICES, NUM_MACHINES, NUM_SERVERS, PROCESS_TIME, COMPUTE_TIME, SEND_INTERVAL))

# Execute!
env.run(until=SIM_TIME)


print([item["waitTime"] for item in time_data])

plt.plot([i["waitTime"] for i in time_data])
plt.ylabel("Wait time of button press in seconds")
plt.show()