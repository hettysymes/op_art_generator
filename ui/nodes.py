import os
from abc import ABC, abstractmethod

import numpy as np
import sympy as sp
from matplotlib.figure import Figure

from Drawing import Drawing
from port_types import PortType
from shapes import Element, Polygon, Ellipse
from ui.Warp import PosWarp, RelWarp, sample_fun
from utils import cubic_f


class PropTypeList:

    def __init__(self, prop_types):
        self.prop_types = prop_types

    def get_default_values(self):
        prop_vals = {}
        for prop_type in self.prop_types:
            prop_vals[prop_type.name] = prop_type.default_value
        return prop_vals

    def __iter__(self):
        return iter(self.prop_types)


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

    def __init__(self, node_id, input_nodes, prop_vals):
        self.node_id = node_id
        self.input_nodes = input_nodes
        self.prop_vals = prop_vals
        self.init_attributes()  # To override
        self.prop_vals = prop_vals if prop_vals else self.prop_type_list.get_default_values()

    def init_attributes(self):
        self.name = "Node"
        self.resizable = True
        self.in_port_types = []
        self.out_port_types = []
        self.prop_type_list = PropTypeList([])

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

    def compute(self):
        return

    def visualise(self, height, wh_ratio):
        return


class CombinationNode(Node):

    def __init__(self, node_id, input_nodes, prop_vals, selection_index):
        self.unit_node = None
        self.selections = None
        self.selection_index = selection_index
        self.init_selections()
        super().__init__(node_id, input_nodes, prop_vals)

    def init_selections(self):
        self.selections = []

    def init_attributes(self):
        self.init_selections()
        self.set_selection(self.selection_index, at_init=True)

    def set_selection(self, index, at_init=False):
        self.selection_index = index
        prop_vals = self.prop_vals if at_init else None
        self.unit_node = self.selections[index](self.node_id, self.input_nodes, prop_vals)
        self.name = self.unit_node.name
        self.resizable = self.unit_node.resizable
        self.in_port_types = self.unit_node.in_port_types
        self.out_port_types = self.unit_node.out_port_types
        self.prop_type_list = self.unit_node.prop_type_list
        if not at_init:
            for k in self.prop_vals:
                if k in self.unit_node.prop_vals:
                    self.unit_node.prop_vals[k] = self.prop_vals[k]
            self.prop_vals = self.unit_node.prop_vals

    def compute(self):
        self.unit_node.input_nodes = self.input_nodes
        self.unit_node.prop_vals = self.prop_vals
        return self.unit_node.compute()

    def visualise(self, height, wh_ratio):
        self.unit_node.input_nodes = self.input_nodes
        self.unit_node.prop_vals = self.prop_vals
        return self.unit_node.visualise(height, wh_ratio)


class CanvasNode(Node):
    DISPLAY = "Canvas"

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)
        self.name = CanvasNode.DISPLAY
        self.resizable = False
        self.in_port_types = [PortType.VISUALISABLE]
        self.prop_type_list = PropTypeList([
            PropType("width", "int", default_value=150, max_value=500, min_value=1,
                     description=""),
            PropType("height", "int", default_value=150, max_value=500, min_value=1,
                     description="")
        ])

    def init_attributes(self):
        self.name = CanvasNode.DISPLAY
        self.resizable = False
        self.in_port_types = [PortType.VISUALISABLE]
        self.out_port_types = []
        self.prop_type_list = PropTypeList([
            PropType("width", "int", default_value=150, max_value=500, min_value=1,
                     description=""),
            PropType("height", "int", default_value=150, max_value=500, min_value=1,
                     description="")
        ])

    def compute(self):
        return self.input_nodes[0].compute()

    def visualise(self, height, wh_ratio):
        return self.input_nodes[0].visualise(height, wh_ratio)


class BlankCanvas(Drawing):

    def __init__(self, out_name, height, wh_ratio):
        super().__init__(out_name, height, wh_ratio)

    def draw(self):
        self.add_bg()

def create_graph_svg(height, wh_ratio, y, filepath):
    # Sample the function (1000 points for smooth curve)
    x = np.linspace(0, 1, len(y))

    # Create a Figure and plot the data
    width = wh_ratio * height
    dpi = 100
    fig = Figure(figsize=(width / dpi, height / dpi), dpi=dpi)
    ax = fig.add_subplot(111)

    # Plot the function with appropriate styling
    ax.plot(x, y, 'b-', linewidth=2)

    ax.set_xlabel("x")
    ax.set_ylabel("y")

    # Add grid for better readability
    ax.grid(True, alpha=0.3)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    fig.savefig(filepath, format='svg', bbox_inches='tight')
    return filepath

class PosWarpNode(UnitNode):
    DISPLAY = "Pos Warp"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def init_attributes(self):
        self.name = PosWarpNode.DISPLAY
        self.resizable = True
        self.in_port_types = [PortType.FUNCTION]
        self.out_port_types = [PortType.WARP]
        self.prop_type_list = PropTypeList([])

    def compute(self):
        f = self.input_nodes[0].compute()
        if f: return PosWarp(f)

    def visualise(self, height, wh_ratio):
        warp = self.compute()
        if warp:
            return create_graph_svg(height, wh_ratio, warp.sample(1000),f"tmp/{str(self.node_id)}")


class RelWarpNode(UnitNode):
    DISPLAY = "Rel Warp"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def init_attributes(self):
        self.name = RelWarpNode.DISPLAY
        self.resizable = True
        self.in_port_types = [PortType.FUNCTION]
        self.out_port_types = [PortType.WARP]
        self.prop_type_list = PropTypeList([])

    def compute(self):
        f = self.input_nodes[0].compute()
        if f: return RelWarp(f)

    def visualise(self, height, wh_ratio):
        warp = self.compute()
        if warp:
            return create_graph_svg(height, wh_ratio, warp.sample(1000), f"tmp/{str(self.node_id)}")


class GridNode(UnitNode):
    DISPLAY = "Grid"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def init_attributes(self):
        self.name = GridNode.DISPLAY
        self.resizable = True
        self.in_port_types = [PortType.WARP, PortType.WARP]
        self.out_port_types = [PortType.GRID]
        self.prop_type_list = PropTypeList(
            [
                PropType("width", "int", default_value=5,
                         description="Number of squares in width of grid"),
                PropType("height", "int", default_value=5,
                         description="Number of squares in height of grid")
            ]
        )

    def compute(self):
        # Get warp functions
        x_warp = self.input_nodes[0].compute()
        if x_warp is None:
            x_warp = PosWarp(lambda i: i)
        else:
            assert isinstance(x_warp, PosWarp) or isinstance(x_warp, RelWarp)

        y_warp = self.input_nodes[1].compute()
        if y_warp is None:
            y_warp = PosWarp(lambda i: i)
        else:
            assert isinstance(y_warp, PosWarp) or isinstance(y_warp, RelWarp)

        v_line_xs = x_warp.sample(self.prop_vals['width']+1)
        h_line_ys = y_warp.sample(self.prop_vals['height']+1)
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
    DISPLAY = "Shape Repeater"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)
        self.name = ShapeRepeaterNode.DISPLAY
        self.in_port_types = [PortType.GRID, PortType.ELEMENT]
        self.out_port_types = [PortType.ELEMENT]

    def init_attributes(self):
        self.name = ShapeRepeaterNode.DISPLAY
        self.resizable = True
        self.in_port_types = [PortType.GRID, PortType.ELEMENT]
        self.out_port_types = [PortType.ELEMENT]
        self.prop_type_list = PropTypeList([])

    def compute(self):
        grid_out = self.input_nodes[0].compute()
        element = self.input_nodes[1].compute()
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
    DISPLAY = "Polygon"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def init_attributes(self):
        self.name = PolygonNode.DISPLAY
        self.resizable = True
        self.in_port_types = []
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
        return Element([Polygon(self.prop_vals['points'], self.prop_vals['fill'], 'none')])

    def visualise(self, height, wh_ratio):
        return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, self.compute()).save()


class EllipseNode(UnitNode):
    DISPLAY = "Ellipse"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def init_attributes(self):
        self.name = EllipseNode.DISPLAY
        self.resizable = True
        self.in_port_types = []
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
        return Element(
            [Ellipse((0.5, 0.5), (self.prop_vals['rx'], self.prop_vals['ry']), self.prop_vals['fill'], 'none')])

    def visualise(self, height, wh_ratio):
        return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, self.compute()).save()


class CheckerboardNode(UnitNode):
    DISPLAY = "Checkerboard"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def init_attributes(self):
        self.name = CheckerboardNode.DISPLAY
        self.resizable = True
        self.in_port_types = [PortType.GRID, PortType.ELEMENT, PortType.ELEMENT]
        self.out_port_types = [PortType.ELEMENT]
        self.prop_type_list = PropTypeList([])

    def compute(self):
        grid_out = self.input_nodes[0].compute()
        element1 = self.input_nodes[1].compute()
        element2 = self.input_nodes[2].compute()
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
    DISPLAY = "Cubic Function"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def init_attributes(self):
        self.name = CubicFunNode.DISPLAY
        self.resizable = True
        self.in_port_types = []
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
        return cubic_f(self.prop_vals['a_coeff'], self.prop_vals['b_coeff'], self.prop_vals['c_coeff'],
                       self.prop_vals['d_coeff'])

    def visualise(self, height, wh_ratio):
        function = self.compute()
        if function:
            return create_graph_svg(height, wh_ratio, sample_fun(function, 1000),f"tmp/{str(self.node_id)}")


class CustomFunNode(UnitNode):
    DISPLAY = "Custom Function"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def init_attributes(self):
        self.name = CustomFunNode.DISPLAY
        self.resizable = True
        self.in_port_types = []
        self.out_port_types = [PortType.FUNCTION]
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
            return create_graph_svg(height, wh_ratio, sample_fun(function, 1000),f"tmp/{str(self.node_id)}")

class PiecewiseFunNode(UnitNode):
    DISPLAY = "Piecewise Function"

    def __init__(self, node_id, input_nodes, prop_vals):
        super().__init__(node_id, input_nodes, prop_vals)

    def init_attributes(self):
        self.name = PiecewiseFunNode.DISPLAY
        self.resizable = True
        self.in_port_types = []
        self.out_port_types = [PortType.FUNCTION]
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
            return create_graph_svg(height, wh_ratio, sample_fun(function, 1000),f"tmp/{str(self.node_id)}")

class ShapeNode(CombinationNode):
    DISPLAY = "Shape"
    SELECTIONS = [PolygonNode, EllipseNode]

    def __init__(self, node_id, input_nodes, properties, selection_index):
        super().__init__(node_id, input_nodes, properties, selection_index)

    def init_selections(self):
        self.selections = ShapeNode.SELECTIONS


class WarpNode(CombinationNode):
    DISPLAY = "Warp"
    SELECTIONS = [PosWarpNode, RelWarpNode]

    def __init__(self, node_id, input_nodes, properties, selection_index):
        super().__init__(node_id, input_nodes, properties, selection_index)

    def init_selections(self):
        self.selections = WarpNode.SELECTIONS


class FunctionNode(CombinationNode):
    DISPLAY = "Function"
    SELECTIONS = [CubicFunNode, PiecewiseFunNode, CustomFunNode]

    def __init__(self, node_id, input_nodes, properties, selection_index):
        super().__init__(node_id, input_nodes, properties, selection_index)

    def init_selections(self):
        self.selections = FunctionNode.SELECTIONS


node_classes = [GridNode, ShapeNode, ShapeRepeaterNode, CheckerboardNode, WarpNode,
                FunctionNode, CanvasNode]
