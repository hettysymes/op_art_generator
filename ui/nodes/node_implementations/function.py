import sympy as sp

from ui.nodes.drawers.draw_graph import create_graph_svg
from ui.nodes.function_datatypes import PiecewiseFun, CustomFun, CubicFun
from ui.nodes.node_defs import NodeInfo
from ui.nodes.nodes import UnitNode, CombinationNode
from ui.nodes.port_defs import PortIO, PortDef, PT_Function, PropEntry, PT_Float, PT_String, PT_PointRefTable
from ui.nodes.warp_datatypes import sample_fun
from ui.vis_types import MatplotlibFig

DEF_CUBIC_FUN_INFO = NodeInfo(
    description="Define a cubic function.",
    port_defs={
        (PortIO.OUTPUT, '_main'): PortDef("Function", PT_Function())
    },
    prop_entries={
        'a_coeff': PropEntry(PT_Float(),
                             display_name="x³ coefficient",
                             description="x³ coefficient (i.e. a in the expression ax³ + bx² + cx + d).",
                             default_value=3.22),
        'b_coeff': PropEntry(PT_Float(),
                             display_name="x² coefficient",
                             description="x² coefficient (i.e. b in the expression ax³ + bx² + cx + d).",
                             default_value=-5.41),
        'c_coeff': PropEntry(PT_Float(),
                             display_name="x coefficient",
                             description="x coefficient ( i.e. c in the expression ax³ + bx² + cx + d).",
                             default_value=3.20),
        'd_coeff': PropEntry(PT_Float(),
                             display_name="Constant",
                             description="Constant (i.e. d in the expression ax³ + bx² + cx + d).",
                             default_value=0)
    }
)


class CubicFunNode(UnitNode):
    NAME = "Cubic Function"
    DEFAULT_NODE_INFO = DEF_CUBIC_FUN_INFO

    def compute(self):
        self.set_compute_result(
            CubicFun(self._prop_val('a_coeff'), self._prop_val('b_coeff'), self._prop_val('c_coeff'),
                     self._prop_val('d_coeff')))

    def visualise(self):
        return MatplotlibFig(create_graph_svg(sample_fun(self.get_compute_result(), 1000)))


DEF_CUSTOM_FUN_INFO = NodeInfo(
    description="Define a custom function by entering an equation in terms of x.",
    port_defs={
        (PortIO.OUTPUT, '_main'): PortDef("Function", PT_Function())
    },
    prop_entries={
        'fun_def': PropEntry(PT_String(),
                             display_name="f(x) =",
                             description="Custom function f(x) defined in terms of x.",
                             default_value="x",
                             auto_format=False)
    }
)


class CustomFunNode(UnitNode):
    NAME = "Custom Function"
    DEFAULT_NODE_INFO = DEF_CUSTOM_FUN_INFO

    def compute(self):
        x = sp.symbols('x')
        parsed_expr = sp.sympify(self._prop_val('fun_def'))
        self.set_compute_result(CustomFun(x, parsed_expr))

    def visualise(self):
        return MatplotlibFig(create_graph_svg(sample_fun(self.get_compute_result(), 1000)))


DEF_PIECEWISE_FUN_INFO = NodeInfo(
    description="Define a piecewise linear function by entering points the function passes through.",
    port_defs={
        (PortIO.OUTPUT, '_main'): PortDef("Function", PT_Function())
    },
    prop_entries={
        'points': PropEntry(PT_PointRefTable(),
                            display_name="Points",
                            description="Points defining where the piecewise linear function passes through.",
                            default_value=[(0, 0), (0.5, 0.5), (1, 1)])
    }
)


class PiecewiseFunNode(UnitNode):
    NAME = "Piecewise Linear Function"
    DEFAULT_NODE_INFO = DEF_PIECEWISE_FUN_INFO

    def compute(self):
        xs, ys = zip(*self._prop_val('points'))
        self.set_compute_result(PiecewiseFun(xs, ys))

    def visualise(self):
        return MatplotlibFig(create_graph_svg(sample_fun(self.get_compute_result(), 1000)))


class FunctionNode(CombinationNode):
    NAME = "Function"
    SELECTIONS = [CubicFunNode, PiecewiseFunNode, CustomFunNode]
