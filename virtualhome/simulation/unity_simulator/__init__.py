from .comm_unity import UnityCommunication
import glob
import sys
from sys import platform

# Needs to be fixed!
original_path = sys.path[5]
new_path = "/mnt/disk1/decom/virtualhome/virtualhome/simulation"
sys.path.append(new_path)

from unity_simulator.comm_unity import UnityCommunication
from unity_simulator import utils_viz
