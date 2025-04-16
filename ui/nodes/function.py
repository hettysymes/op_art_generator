import numpy as np

from ui.nodes.drawers.draw_graph import create_graph_svg
from ui.nodes.nodes import UnitNode, CombinationNode, PropTypeList, PropType
from ui.nodes.warp_utils import sample_fun
from ui.port_defs import PortDef, PortType


class CubicFunNode(UnitNode):
    DISPLAY = "Cubic Function"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def init_attributes(self):
        self.name = CubicFunNode.DISPLAY
        self.resizable = True
        self.in_port_defs = []
        self.out_port_defs = [PortDef("Function", PortType.FUNCTION)]
        self.prop_type_list = PropTypeList(
            [
                PropType("a_coeff", "float", default_value=3.22,
                         description=""),
                PropType("b_coeff", "float", default_value=-5.41,
                         description=""),
                PropType("c_coeff", "float", default_value=3.20,
                         description=""),
                PropType("d_coeff", "float", default_value=0,
                         description="")
            ]
        )

    def compute(self):
        return cubic_f(self.prop_vals['a_coeff'], self.prop_vals['b_coeff'], self.prop_vals['c_coeff'],
                       self.prop_vals['d_coeff'])

    def visualise(self, height, wh_ratio):
        function = self.compute()
        if function:
            return create_graph_svg(height, wh_ratio, sample_fun(function, 1000), f"tmp/{str(self.node_id)}")


class CustomFunNode(UnitNode):
    DISPLAY = "Custom Function"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def init_attributes(self):
        self.name = CustomFunNode.DISPLAY
        self.resizable = True
        self.in_port_defs = []
        self.out_port_defs = [PortDef("Function", PortType.FUNCTION)]
        self.prop_type_list = PropTypeList(
            [
                PropType("fun_def", "string", default_value="x",
                         description="")
            ]
        )

    def compute(self):
        x = sp.symbols('x')
        parsed_expr = sp.sympify(self.prop_vals['fun_def'])
        return sp.lambdify(x, parsed_expr)

    def visualise(self, height, wh_ratio):
        function = self.compute()
        if function:
            return create_graph_svg(height, wh_ratio, sample_fun(function, 1000), f"tmp/{str(self.node_id)}")


class PiecewiseFunNode(UnitNode):
    DISPLAY = "Piecewise Function"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def init_attributes(self):
        self.name = PiecewiseFunNode.DISPLAY
        self.resizable = True
        self.in_port_defs = []
        self.out_port_defs = [PortDef("Function", PortType.FUNCTION)]
        self.prop_type_list = PropTypeList(
            [
                PropType("points", "table", default_value=[(0, 0), (0.5, 0.5), (1, 1)],
                         description="")
            ]
        )

    def compute(self):
        xs, ys = zip(*self.prop_vals['points'])
        return lambda i: np.interp(i, xs, ys)

    def visualise(self, height, wh_ratio):
        function = self.compute()
        if function:
            return create_graph_svg(height, wh_ratio, sample_fun(function, 1000), f"tmp/{str(self.node_id)}")


class FunctionNode(CombinationNode):
    DISPLAY = "Function"
    SELECTIONS = [CubicFunNode, PiecewiseFunNode, CustomFunNode]

    def __init__(self, node_id, input_nodes, properties, selection_index):
        super().__init__(node_id, input_nodes, properties, selection_index)

    def init_selections(self):
        self.selections = FunctionNode.SELECTIONS
