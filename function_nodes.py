from utils import cubic_f
from port_types import PortType
import sympy as sp
import numpy as np

class CubicFunNode:
    INPUT_PORTS = []
    OUTPUT_PORTS = [PortType.FUNCTION]

    def __init__(self, node_id, input_nodes, properties):
        self.node_id = node_id
        self.a_coeff = properties['a_coeff']
        self.b_coeff = properties['b_coeff']
        self.c_coeff = properties['c_coeff']
        self.d_coeff = properties['d_coeff']

    def compute(self):
        return cubic_f(self.a_coeff, self.b_coeff, self.c_coeff, self.d_coeff)

    def visualise(self, height, wh_ratio):
        return
    
class CustomFunNode:
    INPUT_PORTS = []
    OUTPUT_PORTS = [PortType.FUNCTION]

    def __init__(self, node_id, input_nodes, properties):
        self.node_id = node_id
        self.fun_def = properties['fun_def']

    def compute(self):
        x = sp.symbols('x')
        parsed_expr = sp.sympify(self.fun_def)
        return sp.lambdify(x, parsed_expr)

    def visualise(self, height, wh_ratio):
        return
    
class PiecewiseFunNode:
    INPUT_PORTS = []
    OUTPUT_PORTS = [PortType.FUNCTION]

    def __init__(self, node_id, input_nodes, properties):
        self.node_id = node_id
        self.points = properties['points']

    def compute(self):
        xs, ys = zip(*self.points)
        return lambda i: np.interp(i, xs, ys)

    def visualise(self, height, wh_ratio):
        return