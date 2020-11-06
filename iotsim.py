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

# All times unless otherwise specified are in half a second

RANDOM_SEED = 42                 # Not so random but we want it reproducible
NUM_MACHINES = 1                 # Number of available machines in the cloud.
NUM_CORES = 4                    # Number of cpu cores on the raspberry pi.
NUM_DEVICES = 10                 # Number of edge devices
PROCESS_TIME = 8                 # Time it takes to calculate 
SEND_TO_CLOUD_TIME = 1           # Time it takes for a heavy calculation
SEND_INTERVAL = 20               # How often a edge device will send a bulk of five images.
SIM_TIME = 4000                  # Simulation time in seconds

time_data = []          # List of dictionaries to store the data of how long a request takes.

class Cloud(object):
    """
    A cloud with limited number of rented machines A.K.A The cloud.

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

class Gateway(object):
    """
    Our gateway devices, hopefully only one is needed.
    """
    def __init__(self, env, num_servers, processtime, cloud):
        self.env = env
        self.server = simpy.PriorityResource(env, num_servers)
        self.processtime = processtime
        self.cloud = cloud
        self.reqsUntilSend = 10

    def proc(self, val):
        """
        Processing the data incoming from a IOT device.
        """

        #Every 10 requests we also send data to the cloud.
        if self.reqsUntilSend <= 0:
            self.reqsUntilSend = 10
            print("Gateway is sending data to the cloud!")
            yield self.env.timeout(self.processtime)
            yield env.process(self.cloud.calc(val))
        else:
            # Every other when we don't send data to the cloud.
            self.reqsUntilSend = self.reqsUntilSend - 1
            yield self.env.timeout(self.processtime)


def device(env, name, gateway):
    """The device process (each device has a ``name``) sends a request for data
    from (``server``).

    It then starts the calculation process and waits for it to finish...

    """
    
    starttime = env.now
    with gateway.server.request() as request:
        yield request

        getsprocessed = env.now
        yield env.process(gateway.proc(name))

        getsanswered = env.now
        wt = getsprocessed - starttime
        pt = getsanswered - getsprocessed
        tt = getsanswered - starttime
        time_data.append({"waitTime": wt*2, "processTime": pt*2, "totalTime": tt*2})

def setup(env, num_devices, num_machines, num_cores, processtime, computetime, t_inter):
    """Create a cloud, a number of servers, a number of initial device requests and keep creating cars
    approx. every ``t_inter`` minutes."""
    # Create the Cloud object
    cloud = Cloud(env, num_machines, computetime)

    # Create the Gateway system
    gateway = Gateway(env, num_cores, processtime, cloud)

    i=0
    # Create more iot data requests while the simulation is running
    while True:
        yield env.timeout(t_inter/num_devices)
        i+=1
        env.process(device(env, 'IOT %d' % (i%num_devices), gateway))

# Setup and start the simulation
print('IOT Network simulation')

random.seed(RANDOM_SEED)  # This helps reproducing the results

# Create an environment and start the setup process
env = simpy.Environment()
env.process(setup(env, NUM_DEVICES, NUM_MACHINES, NUM_CORES, PROCESS_TIME, SEND_TO_CLOUD_TIME, SEND_INTERVAL))

# Execute!
env.run(until=SIM_TIME)


print([item["waitTime"] for item in time_data])

plt.plot([i["waitTime"] for i in time_data])
plt.ylabel("Wait time of button press in seconds")
plt.show()
