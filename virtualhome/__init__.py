import glob
import sys
from sys import platform

import os
curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(curr_dir, 'simulation'))

from unity_simulator.comm_unity import UnityCommunication
from unity_simulator import utils_viz