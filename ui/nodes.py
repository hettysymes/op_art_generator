from abc import ABC, abstractmethod

import numpy as np
import sympy as sp

from Drawing import Drawing
from port_types import PortType
from shapes import Element, Polygon, Ellipse
from ui.Warp import PosWarp, RelWarp
from utils import cubic_f


class PropTypeList:

    def __init__(self, prop_types):
        self.prop_types = prop_types

    def get_default_values(self):
        prop_vals = {}
        for prop_type in self.prop_types:
            prop_vals[prop_type.name] = prop_type.default_value
        return prop_vals


class PropType:
    """Defines a property for a node"""

    def __init__(self, name, prop_type, default_value=None, min_value=None, max_value=None,
                 options=None, description=""):
        self.name = name
        self.prop_type = prop_type  # "int", "float", "string", "bool", "enum"
        self.default_value = default_value
        self.min_value = min_value
        self.max_value = max_value
        self.options = options  # For enum type
        self.description = description


class Node(ABC):

    def __init__(self, node_id, input_nodes=None, prop_vals=None):
        self.node_id = node_id
        self.input_nodes = input_nodes
        self.prop_vals = prop_vals

        # To override
        self.name = "Node"
        self.resizable = True
        self.in_port_types = []
        self.out_port_types = []
        self.prop_type_list = None

    def get_prop_vals(self):
        if not self.prop_vals:
            self.prop_vals = self.prop_type_list.get_default_values()
        return self.prop_vals

    def get_svg_path(self, height, wh_ratio):
        vis = self.visualise(height, wh_ratio)
        if vis: return vis
        # No visualisation, return blank canvas
        return BlankCanvas(f"tmp/{str(self.node_id)}", height, wh_ratio).save()

    @abstractmethod
    def compute(self):
        pass

    @abstractmethod
    def visualise(self, height, wh_ratio):
        pass


class UnitNode(Node):

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)
        self.name = "Empty"

    def compute(self):
        return

    def visualise(self, height, wh_ratio):
        return


class CombinationNode(Node):

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)
        self.unit_node = None
        self.selections = [] # To override
        # Set selection here

    def set_selection(self, index):
        self.input_nodes = None
        self.prop_vals = None
        self.unit_node = self.selections[index](self.node_id, None, None)

        self.name = self.unit_node.name
        self.resizable = self.unit_node.resizable
        self.in_port_types = self.unit_node.in_port_types
        self.out_port_types = self.unit_node.out_port_types
        self.prop_type_list = self.unit_node.prop_type_list

    def compute(self):
        return self.unit_node.compute()

    def visualise(self, height, wh_ratio):
        return self.unit_node.visualise(height, wh_ratio)


class CanvasNode(Node):

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)
        self.name = "Canvas"
        self.resizable = False
        self.in_port_types = [PortType.VISUALISABLE]
        self.prop_type_list = PropTypeList([
            PropType("width", "int", default_value=150, max_value=500, min_value=1,
                     description=""),
            PropType("height", "int", default_value=150, max_value=500, min_value=1,
                     description="")
        ])

        self.input_node = input_nodes[0]

    def compute(self):
        return self.input_node.compute()

    def visualise(self, height, wh_ratio):
        return self.input_node.visualise(height, wh_ratio)


class BlankCanvas(Drawing):

    def __init__(self, out_name, height, wh_ratio):
        super().__init__(out_name, height, wh_ratio)

    def draw(self):
        self.add_bg()


class PosWarpNode(UnitNode):

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)
        self.name = "Pos Warp"
        self.in_port_types = [PortType.FUNCTION]
        self.out_port_types = [PortType.WARP]

        self.f_node = input_nodes[0]

    def compute(self):
        f = self.f_node.compute()
        if f: return PosWarp(f)


class RelWarpNode(UnitNode):

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)
        self.name = "Rel Warp"
        self.in_port_types = [PortType.FUNCTION]
        self.out_port_types = [PortType.WARP]

        self.f_node = input_nodes[0]

    def compute(self):
        f = self.f_node.compute()
        if f: return RelWarp(f)


class GridNode(UnitNode):

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)
        self.name = "Grid"
        self.in_port_types = [PortType.WARP, PortType.WARP]
        self.out_port_types = [PortType.GRID]
        self.prop_type_list = PropTypeList(
            [
                PropType("num_v_lines", "int", default_value=5,
                         description="Number of squares in width of grid"),
                PropType("num_h_lines", "int", default_value=5,
                         description="Number of squares in height of grid")
            ]
        )
        self.x_warp_node, self.y_warp_node = input_nodes

    def compute(self):
        # Get warp functions
        x_warp = self.x_warp_node.compute()
        if x_warp is None:
            x_warp = PosWarp(lambda i: i)
        else:
            assert isinstance(x_warp, PosWarp) or isinstance(x_warp, RelWarp)

        y_warp = self.y_warp_node.compute()
        if y_warp is None:
            y_warp = PosWarp(lambda i: i)
        else:
            assert isinstance(y_warp, PosWarp) or isinstance(y_warp, RelWarp)

        prop_vals = self.get_prop_vals()
        v_line_xs = x_warp.sample(prop_vals['num_v_lines'])
        h_line_ys = y_warp.sample(prop_vals['num_h_lines'])
        return v_line_xs, h_line_ys

    def visualise(self, height, wh_ratio):
        return GridDrawing(f"tmp/{str(self.node_id)}", height, wh_ratio, self.compute()).save()


class GridDrawing(Drawing):

    def __init__(self, out_name, height, wh_ratio, inputs):
        super().__init__(out_name, height, wh_ratio)
        self.v_line_xs, self.h_line_ys = inputs
        self.v_line_xs *= self.width
        self.h_line_ys *= self.height

    def draw(self):
        self.add_bg()
        for x in self.v_line_xs:
            # Draw vertical line
            self.dwg_add(self.dwg.line((x, 0), (x, self.height), stroke='black'))
        for y in self.h_line_ys:
            # Draw horizontal line
            self.dwg_add(self.dwg.line((0, y), (self.width, y), stroke='black'))


class ShapeRepeaterNode(UnitNode):

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)
        self.name = "Shape Repeater"
        self.in_port_types = [PortType.GRID, PortType.ELEMENT]
        self.out_port_types = [PortType.ELEMENT]

        self.grid_node = input_nodes[0]
        self.element_node = input_nodes[1]

    def compute(self):
        grid_out = self.grid_node.compute()
        element = self.element_node.compute()
        if grid_out and element:
            v_line_xs, h_line_ys = grid_out
            ret_element = Element()
            for i in range(1, len(v_line_xs)):
                for j in range(1, len(h_line_ys)):
                    x1 = v_line_xs[i - 1]
                    x2 = v_line_xs[i]
                    y1 = h_line_ys[j - 1]
                    y2 = h_line_ys[j]
                    for shape in element:
                        ret_element.add(shape.scale(x2 - x1, y2 - y1).translate(x1, y1))
            return ret_element

    def visualise(self, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, element).save()


class ElementDrawer(Drawing):

    def __init__(self, out_name, height, wh_ratio, inputs):
        super().__init__(out_name, height, wh_ratio)
        assert isinstance(inputs, Element)
        self.element = inputs

    def draw(self):
        self.add_bg()
        for shape in self.element:
            self.dwg_add(shape.scale(self.width, self.height).get(self.dwg))


class PolygonNode(UnitNode):

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)
        self.name = "Polygon"
        self.out_port_types = [PortType.ELEMENT]
        self.prop_type_list = PropTypeList(
            [
                PropType("points", "table", default_value=[(0, 0), (0, 1), (1, 1)],
                         description=""),
                PropType("fill", "string", default_value="black",
                         description="")
            ]
        )

    def compute(self):
        prop_vals = self.get_prop_vals()
        return Element([Polygon(prop_vals['points'], prop_vals['fill'], 'none')])

    def visualise(self, height, wh_ratio):
        return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, self.compute()).save()


class EllipseNode(UnitNode):

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)
        self.name = "Ellipse"
        self.out_port_types = [PortType.ELEMENT]
        self.prop_type_list = PropTypeList(
            [
                PropType("rx", "float", default_value=0.5,
                         description=""),
                PropType("ry", "float", default_value=0.5,
                         description=""),
                PropType("fill", "string", default_value="black",
                         description="")
            ]
        )

    def compute(self):
        prop_vals = self.get_prop_vals()
        return Element([Ellipse((0.5, 0.5), (prop_vals['rx'], prop_vals['ry']), prop_vals['fill'], 'none')])

    def visualise(self, height, wh_ratio):
        return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, self.compute()).save()


class CheckerboardNode(UnitNode):

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)
        self.name = "Checkerboard"
        self.in_port_types = [PortType.GRID, PortType.ELEMENT, PortType.ELEMENT]
        self.out_port_types = [PortType.ELEMENT]

        self.grid_node = input_nodes[0]
        self.element1_node = input_nodes[1]
        self.element2_node = input_nodes[2]

    def compute(self):
        grid_out = self.grid_node.compute()
        element1 = self.element1_node.compute()
        element2 = self.element2_node.compute()
        if grid_out and element1 and element2:
            v_line_xs, h_line_ys = grid_out
            ret_element = Element()
            element1_starts = True
            for i in range(1, len(v_line_xs)):
                element1_turn = element1_starts
                for j in range(1, len(h_line_ys)):
                    x1 = v_line_xs[i - 1]
                    x2 = v_line_xs[i]
                    y1 = h_line_ys[j - 1]
                    y2 = h_line_ys[j]
                    element = element1 if element1_turn else element2
                    for shape in element:
                        ret_element.add(shape.scale(x2 - x1, y2 - y1).translate(x1, y1))
                    element1_turn = not element1_turn
                element1_starts = not element1_starts
            return ret_element

    def visualise(self, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, element).save()


class CubicFunNode(UnitNode):

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)
        self.name = "Cubic Function"
        self.out_port_types = [PortType.FUNCTION]
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
        prop_vals = self.get_prop_vals()
        return cubic_f(prop_vals['a_coeff'], prop_vals['b_coeff'], prop_vals['c_coeff'], prop_vals['d_coeff'])


class CustomFunNode(UnitNode):

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)
        self.name = "Custom Function"
        self.out_port_types = [PortType.FUNCTION]
        self.prop_type_list = PropTypeList(
            [
                PropType("fun_def", "string", default_value="x",
                         description="")
            ]
        )

    def compute(self):
        prop_vals = self.get_prop_vals()
        x = sp.symbols('x')
        parsed_expr = sp.sympify(prop_vals['fun_def'])
        return sp.lambdify(x, parsed_expr)


class PiecewiseFunNode(UnitNode):

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)
        self.name = "Piecewise Function"
        self.out_port_types = [PortType.FUNCTION]
        self.prop_type_list = PropTypeList(
            [
                PropType("points", "table", default_value=[(0, 0), (0.5, 0.5), (1, 1)],
                         description="")
            ]
        )

    def compute(self):
        prop_vals = self.get_prop_vals()
        xs, ys = zip(*prop_vals['points'])
        return lambda i: np.interp(i, xs, ys)


class ShapeNode(CombinationNode):

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)
        self.selections = [PolygonNode, EllipseNode]
        self.set_selection(0)


node_classes = [CanvasNode, PosWarpNode, RelWarpNode, GridNode, ShapeRepeaterNode, ShapeNode,
                CheckerboardNode,
                CubicFunNode, CustomFunNode, PiecewiseFunNode]
