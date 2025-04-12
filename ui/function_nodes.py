from ui.nodes import Node, NodeProperty
from utils import cubic_f
from port_types import PortType
import sympy as sp
import numpy as np

class CubicFunNode(Node):
    INPUT_PORTS = []
    OUTPUT_PORTS = [PortType.FUNCTION]
    NAME = "Cubic Function"
    PROPERTIES = [
        NodeProperty("a_coeff", "float", default_value=3.22,
                    description=""),
        NodeProperty("b_coeff", "float", default_value=-5.41,
                    description=""),
        NodeProperty("c_coeff", "float", default_value=3.20,
                    description=""),
        NodeProperty("d_coeff", "float", default_value=0,
                    description="")
    ]

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)
        self.a_coeff = properties['a_coeff']
        self.b_coeff = properties['b_coeff']
        self.c_coeff = properties['c_coeff']
        self.d_coeff = properties['d_coeff']

    def compute(self):
        return cubic_f(self.a_coeff, self.b_coeff, self.c_coeff, self.d_coeff)

    def visualise(self, height, wh_ratio):
        return
    
class CustomFunNode(Node):
    INPUT_PORTS = []
    OUTPUT_PORTS = [PortType.FUNCTION]
    NAME = "Custom Function"
    PROPERTIES = [
        NodeProperty("fun_def", "string", default_value="x",
                    description="")
    ]

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)
        self.fun_def = properties['fun_def']

    def compute(self):
        x = sp.symbols('x')
        parsed_expr = sp.sympify(self.fun_def)
        return sp.lambdify(x, parsed_expr)

    def visualise(self, height, wh_ratio):
        return
    
class PiecewiseFunNode(Node):
    INPUT_PORTS = []
    OUTPUT_PORTS = [PortType.FUNCTION]
    NAME = "Piecewise Function"
    PROPERTIES = [
        NodeProperty("points", "table", default_value=[(0, 0), (0.5, 0.5), (1, 1)],
                    description="")
    ]

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)
        self.points = properties['points']

    def compute(self):
        xs, ys = zip(*self.points)
        return lambda i: np.interp(i, xs, ys)

    def visualise(self, height, wh_ratio):
        return