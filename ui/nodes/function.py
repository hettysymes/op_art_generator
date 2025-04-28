import numpy as np
import sympy as sp

from ui.nodes.drawers.draw_graph import create_graph_svg
from ui.nodes.nodes import UnitNode, CombinationNode, UnitNodeInfo, PropTypeList, PropType
from ui.nodes.utils import cubic_f
from ui.nodes.warp_utils import sample_fun
from ui.port_defs import PortDef, PortType, PT_Function

CUBIC_FUN_NODE_INFO = UnitNodeInfo(
    name="Cubic Function",
    resizable=True,
    selectable=False,
    in_port_defs=[],
    out_port_defs=[PortDef("Function", PT_Function)],
    prop_type_list=PropTypeList(
        [
            PropType("a_coeff", "float", default_value=3.22,
                     description="x³ coefficient (i.e. a in the expression ax³ + bx² + cx + d).", display_name="x³ coefficient"),
            PropType("b_coeff", "float", default_value=-5.41,
                     description="x² coefficient (i.e. b in the expression ax³ + bx² + cx + d).", display_name="x² coefficient"),
            PropType("c_coeff", "float", default_value=3.20,
                     description="x coefficient ( i.e. c in the expression ax³ + bx² + cx + d).", display_name="x coefficient"),
            PropType("d_coeff", "float", default_value=0,
                     description="Constant (i.e. d in the expression ax³ + bx² + cx + d).", display_name="Constant")
        ]
    ),
    description="Define a cubic function."
)


class CubicFunNode(UnitNode):
    UNIT_NODE_INFO = CUBIC_FUN_NODE_INFO

    def compute(self):
        return cubic_f(self.prop_vals['a_coeff'], self.prop_vals['b_coeff'], self.prop_vals['c_coeff'],
                       self.prop_vals['d_coeff'])

    def visualise(self, temp_dir, height, wh_ratio):
        function = self.compute()
        if function:
            return create_graph_svg(height, wh_ratio, sample_fun(function, 1000), self._return_path(temp_dir))


CUSTOM_FUN_NODE_INFO = UnitNodeInfo(
    name="Custom Function",
    resizable=True,
    selectable=False,
    in_port_defs=[],
    out_port_defs=[PortDef("Function", PT_Function)],
    prop_type_list=PropTypeList(
        [
            PropType("fun_def", "string", default_value="x",
                     description="Custom function f(x) defined in terms of x.", display_name="f(x) =", auto_format=False)
        ]
    ),
    description="Define a custom function by entering an equation in terms of x."
)


class CustomFunNode(UnitNode):
    UNIT_NODE_INFO = CUSTOM_FUN_NODE_INFO

    def compute(self):
        x = sp.symbols('x')
        parsed_expr = sp.sympify(self.prop_vals['fun_def'])
        return sp.lambdify(x, parsed_expr)

    def visualise(self, temp_dir, height, wh_ratio):
        function = self.compute()
        if function:
            return create_graph_svg(height, wh_ratio, sample_fun(function, 1000), self._return_path(temp_dir))


PIECEWISE_FUN_NODE_INFO = UnitNodeInfo(
    name="Piecewise Linear Function",
    resizable=True,
    selectable=False,
    in_port_defs=[],
    out_port_defs=[PortDef("Function", PT_Function)],
    prop_type_list=PropTypeList(
        [
            PropType("points", "point_table", default_value=[(0, 0), (0.5, 0.5), (1, 1)],
                     description="Points defining where the piecewise linear function passes through.", display_name="Points")
        ]
    ),
    description="Define a piecewise linear function by entering points the function passes through."
)


class PiecewiseFunNode(UnitNode):
    UNIT_NODE_INFO = PIECEWISE_FUN_NODE_INFO

    def compute(self):
        xs, ys = zip(*self.prop_vals['points'])
        return lambda i: np.interp(i, xs, ys)

    def visualise(self, temp_dir, height, wh_ratio):
        function = self.compute()
        if function:
            return create_graph_svg(height, wh_ratio, sample_fun(function, 1000), self._return_path(temp_dir))


class FunctionNode(CombinationNode):
    NAME = "Function"
    SELECTIONS = [CubicFunNode, PiecewiseFunNode, CustomFunNode]
