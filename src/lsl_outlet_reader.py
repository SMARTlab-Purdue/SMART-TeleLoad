import numpy as np
import time
from pylsl import *

# =========== Create LSL Inlets ===============
inlet_info = resolve_byprop('name', "teleload_exp_status", 1, timeout=1) 
# create a new inlet to read from the stream
inlet = StreamInlet(inlet_info[0])


start_time = local_clock()           # Time of the 0th chunk
print("now sending data...")
try:
    while True:
        sample, timestamp = inlet.pull_sample()
        print(sample)

except KeyboardInterrupt:
    pass