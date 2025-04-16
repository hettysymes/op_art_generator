import numpy as np
import sympy as sp

from ui.nodes.drawers.draw_graph import create_graph_svg
from ui.nodes.node_info import CUBIC_FUN_NODE_INFO, CUSTOM_FUN_NODE_INFO, PIECEWISE_FUN_NODE_INFO
from ui.nodes.nodes import UnitNode, CombinationNode
from ui.nodes.utils import cubic_f
from ui.nodes.warp_utils import sample_fun


class CubicFunNode(UnitNode):
    UNIT_NODE_INFO = CUBIC_FUN_NODE_INFO

    def compute(self):
        return cubic_f(self.prop_vals['a_coeff'], self.prop_vals['b_coeff'], self.prop_vals['c_coeff'],
                       self.prop_vals['d_coeff'])

    def visualise(self, height, wh_ratio):
        function = self.compute()
        if function:
            return create_graph_svg(height, wh_ratio, sample_fun(function, 1000), f"tmp/{str(self.node_id)}")


class CustomFunNode(UnitNode):
    UNIT_NODE_INFO = CUSTOM_FUN_NODE_INFO

    def compute(self):
        x = sp.symbols('x')
        parsed_expr = sp.sympify(self.prop_vals['fun_def'])
        return sp.lambdify(x, parsed_expr)

    def visualise(self, height, wh_ratio):
        function = self.compute()
        if function:
            return create_graph_svg(height, wh_ratio, sample_fun(function, 1000), f"tmp/{str(self.node_id)}")


class PiecewiseFunNode(UnitNode):
    UNIT_NODE_INFO = PIECEWISE_FUN_NODE_INFO

    def compute(self):
        xs, ys = zip(*self.prop_vals['points'])
        return lambda i: np.interp(i, xs, ys)

    def visualise(self, height, wh_ratio):
        function = self.compute()
        if function:
            return create_graph_svg(height, wh_ratio, sample_fun(function, 1000), f"tmp/{str(self.node_id)}")


class FunctionNode(CombinationNode):
    NAME = "Function"
    SELECTIONS = [CubicFunNode, PiecewiseFunNode, CustomFunNode]
