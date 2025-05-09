import numpy as np
import sympy as sp

from ui.nodes.drawers.draw_graph import create_graph_svg
from ui.nodes.node_defs import NodeInfo, PropType, PropEntry
from ui.nodes.nodes import UnitNode, CombinationNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Function
from ui.nodes.utils import cubic_f
from ui.nodes.warp_utils import sample_fun
from ui.vis_types import MatplotlibFig

DEF_CUBIC_FUN_INFO = NodeInfo(
    description="Define a cubic function.",
    port_defs={
        (PortIO.OUTPUT, '_main'): PortDef("Function", PT_Function())
    },
    prop_entries={
        'a_coeff': PropEntry(PropType.FLOAT,
                             display_name="x³ coefficient",
                             description="x³ coefficient (i.e. a in the expression ax³ + bx² + cx + d).",
                             default_value=3.22),
        'b_coeff': PropEntry(PropType.FLOAT,
                             display_name="x² coefficient",
                             description="x² coefficient (i.e. b in the expression ax³ + bx² + cx + d).",
                             default_value=-5.41),
        'c_coeff': PropEntry(PropType.FLOAT,
                             display_name="x coefficient",
                             description="x coefficient ( i.e. c in the expression ax³ + bx² + cx + d).",
                             default_value=3.20),
        'd_coeff': PropEntry(PropType.FLOAT,
                             display_name="Constant",
                             description="Constant (i.e. d in the expression ax³ + bx² + cx + d).",
                             default_value=0)
    }
)


class CubicFunNode(UnitNode):
    NAME = "Cubic Function"
    DEFAULT_NODE_INFO = DEF_CUBIC_FUN_INFO

    def compute(self, out_port_key='_main'):
        return cubic_f(self._prop_val('a_coeff'), self._prop_val('b_coeff'), self._prop_val('c_coeff'),
                       self._prop_val('d_coeff'))

    def visualise(self):
        return MatplotlibFig(create_graph_svg(sample_fun(self.compute(), 1000)))


DEF_CUSTOM_FUN_INFO = NodeInfo(
    description="Define a custom function by entering an equation in terms of x.",
    port_defs={
        (PortIO.OUTPUT, '_main'): PortDef("Function", PT_Function())
    },
    prop_entries={
        'fun_def': PropEntry(PropType.STRING,
                             display_name="f(x) =",
                             description="Custom function f(x) defined in terms of x.",
                             default_value="x",
                             auto_format=False)
    }
)


class CustomFunNode(UnitNode):
    NAME = "Custom Function"
    DEFAULT_NODE_INFO = DEF_CUSTOM_FUN_INFO

    def compute(self, out_port_key='_main'):
        x = sp.symbols('x')
        parsed_expr = sp.sympify(self._prop_val('fun_def'))
        return sp.lambdify(x, parsed_expr)

    def visualise(self):
        return MatplotlibFig(create_graph_svg(sample_fun(self.compute(), 1000)))


DEF_PIECEWISE_FUN_INFO = NodeInfo(
    description="Define a piecewise linear function by entering points the function passes through.",
    port_defs={
        (PortIO.OUTPUT, '_main'): PortDef("Function", PT_Function())
    },
    prop_entries={
        'points': PropEntry(PropType.POINT_TABLE,
                            display_name="Points",
                            description="Points defining where the piecewise linear function passes through.",
                            default_value=[(0, 0), (0.5, 0.5), (1, 1)])
    }
)


class PiecewiseFunNode(UnitNode):
    NAME = "Piecewise Linear Function"
    DEFAULT_NODE_INFO = DEF_PIECEWISE_FUN_INFO

    @staticmethod
    def helper(xs, ys):
        return lambda i: np.interp(i, xs, ys)

    def compute(self, out_port_key='_main'):
        xs, ys = zip(*self._prop_val('points'))
        return PiecewiseFunNode.helper(xs, ys)

    def visualise(self):
        return MatplotlibFig(create_graph_svg(sample_fun(self.compute(), 1000)))


class FunctionNode(CombinationNode):
    NAME = "Function"
    SELECTIONS = [CubicFunNode, PiecewiseFunNode, CustomFunNode]
