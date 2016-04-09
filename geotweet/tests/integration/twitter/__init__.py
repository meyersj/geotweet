import os
from os.path import dirname
import sys


ROOT = dirname(dirname(dirname(os.path.abspath(__file__))))
sys.path.append(ROOT)
