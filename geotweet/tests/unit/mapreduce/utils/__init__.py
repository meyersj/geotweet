import os
from os.path import dirname
import sys


def parent_dir(levels=1):
    parent = current = os.path.abspath(__file__)
    for level in range(0, levels):
        parent = os.path.dirname(parent)
    return parent


ROOT = parent_dir(levels=6)
sys.path.append(ROOT)
