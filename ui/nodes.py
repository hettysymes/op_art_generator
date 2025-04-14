from abc import ABC, abstractmethod

import numpy as np
import sympy as sp

from Drawing import Drawing
from port_types import PortType
from shapes import Element, Polygon, Ellipse
from ui.Warp import PosWarp, RelWarp
from utils import cubic_f


class NodeProperty:
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
    NAME = "Node"
    RESIZABLE = True

    def __init__(self, node_id, input_nodes, properties):
        self.node_id = node_id

    def get_svg_path(self, height, wh_ratio):
        vis = self.visualise(height, wh_ratio)
        if vis: return vis
        # No visualisation, return blank canvas
        return BlankCanvas(f"tmp/{str(self.node_id)}", height, wh_ratio).save()

    @abstractmethod
    def input_ports(self):
        pass

    @abstractmethod
    def output_ports(self):
        pass

    @abstractmethod
    def properties(self):
        pass

    @abstractmethod
    def compute(self):
        pass

    @abstractmethod
    def visualise(self, height, wh_ratio):
        pass


class UnitNode(Node):
    NAME = "Empty"
    INPUT_PORTS = []
    OUTPUT_PORTS = []
    PROPERTIES = []

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)

    def input_ports(self):
        return UnitNode.INPUT_PORTS

    def output_ports(self):
        return UnitNode.OUTPUT_PORTS

    def properties(self):
        return UnitNode.PROPERTIES

    def compute(self):
        return

    def visualise(self, height, wh_ratio):
        return

class CanvasNode(Node):
    NAME = "Canvas"
    RESIZABLE = False

    INPUT_PORTS = [PortType.VISUALISABLE]
    PROPERTIES = [
        NodeProperty("width", "int", default_value=150, max_value=500, min_value=1,
                     description=""),
        NodeProperty("height", "int", default_value=150, max_value=500, min_value=1,
                     description="")
    ]

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)
        self.input_node = input_nodes[0]

    def input_ports(self):
        return CanvasNode.INPUT_PORTS

    def properties(self):
        return CanvasNode.PROPERTIES

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
    NAME = "Pos Warp"

    INPUT_PORTS = [PortType.FUNCTION]
    OUTPUT_PORTS = [PortType.WARP]

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)
        self.f_node = input_nodes[0]

    def input_ports(self):
        return PosWarpNode.INPUT_PORTS

    def output_ports(self):
        return PosWarpNode.OUTPUT_PORTS

    def compute(self):
        f = self.f_node.compute()
        if f: return PosWarp(f)

    def visualise(self, height, wh_ratio):
        return


class RelWarpNode(UnitNode):
    NAME = "Rel Warp"

    INPUT_PORTS = [PortType.FUNCTION]
    OUTPUT_PORTS = [PortType.WARP]

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)
        self.f_node = input_nodes[0]

    def input_ports(self):
        return RelWarpNode.INPUT_PORTS

    def output_ports(self):
        return RelWarpNode.OUTPUT_PORTS

    def compute(self):
        f = self.f_node.compute()
        if f: return RelWarp(f)

    def visualise(self, height, wh_ratio):
        return


class GridNode(UnitNode):
    NAME = "Grid"

    INPUT_PORTS = [PortType.WARP, PortType.WARP]
    OUTPUT_PORTS = [PortType.GRID]
    PROPERTIES = [
        NodeProperty("num_v_lines", "int", default_value=5,
                     description="Number of squares in width of grid"),
        NodeProperty("num_h_lines", "int", default_value=5,
                     description="Number of squares in height of grid")
    ]

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)
        self.num_v_lines = properties['num_v_lines']
        self.num_h_lines = properties['num_h_lines']
        self.x_warp_node, self.y_warp_node = input_nodes

    def input_ports(self):
        return GridNode.INPUT_PORTS

    def output_ports(self):
        return GridNode.OUTPUT_PORTS

    def properties(self):
        return GridNode.PROPERTIES

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

        v_line_xs = x_warp.sample(self.num_v_lines)
        h_line_ys = y_warp.sample(self.num_h_lines)
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
    NAME = "Shape Repeater"

    INPUT_PORTS = [PortType.GRID, PortType.ELEMENT]
    OUTPUT_PORTS = [PortType.ELEMENT]

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)
        self.grid_node = input_nodes[0]
        self.element_node = input_nodes[1]

    def input_ports(self):
        return ShapeRepeaterNode.INPUT_PORTS

    def output_ports(self):
        return ShapeRepeaterNode.OUTPUT_PORTS

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
    NAME = "Polygon"

    OUTPUT_PORTS = [PortType.ELEMENT]
    PROPERTIES = [
        NodeProperty("points", "table", default_value=[(0, 0), (0, 1), (1, 1)],
                     description=""),
        NodeProperty("fill", "string", default_value="black",
                     description="")
    ]

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)
        self.points = properties['points']
        self.fill = properties['fill']

    def output_ports(self):
        return PolygonNode.OUTPUT_PORTS

    def properties(self):
        return PolygonNode.PROPERTIES

    def compute(self):
        return Element([Polygon(self.points, self.fill, 'none')])

    def visualise(self, height, wh_ratio):
        return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, self.compute()).save()


class EllipseNode(UnitNode):
    NAME = "Ellipse"

    OUTPUT_PORTS = [PortType.ELEMENT]
    PROPERTIES = [
        NodeProperty("rx", "float", default_value=0.5,
                     description=""),
        NodeProperty("ry", "float", default_value=0.5,
                     description=""),
        NodeProperty("fill", "string", default_value="black",
                     description="")
    ]

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)
        self.rx = properties['rx']
        self.ry = properties['ry']
        self.fill = properties['fill']

    def output_ports(self):
        return EllipseNode.OUTPUT_PORTS

    def properties(self):
        return EllipseNode.PROPERTIES

    def compute(self):
        return Element([Ellipse((0.5, 0.5), (self.rx, self.ry), self.fill, 'none')])

    def visualise(self, height, wh_ratio):
        return ElementDrawer(f"tmp/{str(self.node_id)}", height, wh_ratio, self.compute()).save()


class CheckerboardNode(UnitNode):
    NAME = "Checkerboard"

    INPUT_PORTS = [PortType.GRID, PortType.ELEMENT, PortType.ELEMENT]
    OUTPUT_PORTS = [PortType.ELEMENT]

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)
        self.grid_node = input_nodes[0]
        self.element1_node = input_nodes[1]
        self.element2_node = input_nodes[2]

    def input_ports(self):
        return CheckerboardNode.INPUT_PORTS

    def output_ports(self):
        return CheckerboardNode.OUTPUT_PORTS

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
    NAME = "Cubic Function"

    OUTPUT_PORTS = [PortType.FUNCTION]
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

    def output_ports(self):
        return CubicFunNode.OUTPUT_PORTS

    def properties(self):
        return CubicFunNode.PROPERTIES

    def compute(self):
        return cubic_f(self.a_coeff, self.b_coeff, self.c_coeff, self.d_coeff)

    def visualise(self, height, wh_ratio):
        return


class CustomFunNode(UnitNode):
    NAME = "Custom Function"

    OUTPUT_PORTS = [PortType.FUNCTION]
    PROPERTIES = [
        NodeProperty("fun_def", "string", default_value="x",
                     description="")
    ]

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)
        self.fun_def = properties['fun_def']

    def output_ports(self):
        return CustomFunNode.OUTPUT_PORTS

    def properties(self):
        return CustomFunNode.PROPERTIES

    def compute(self):
        x = sp.symbols('x')
        parsed_expr = sp.sympify(self.fun_def)
        return sp.lambdify(x, parsed_expr)

    def visualise(self, height, wh_ratio):
        return


class PiecewiseFunNode(UnitNode):
    NAME = "Piecewise Function"

    OUTPUT_PORTS = [PortType.FUNCTION]
    PROPERTIES = [
        NodeProperty("points", "table", default_value=[(0, 0), (0.5, 0.5), (1, 1)],
                     description="")
    ]

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)
        self.points = properties['points']

    def output_ports(self):
        return PiecewiseFunNode.OUTPUT_PORTS

    def properties(self):
        return PiecewiseFunNode.PROPERTIES

    def compute(self):
        xs, ys = zip(*self.points)
        return lambda i: np.interp(i, xs, ys)

    def visualise(self, height, wh_ratio):
        return


class CombinationNode(Node):
    SELECTIONS = []

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)
        self.node = CombinationNode.SELECTIONS[properties['_selection']](node_id, input_nodes, properties)

    def input_ports(self):
        return self.node.input_ports()

    def output_ports(self):
        return self.node.output_ports()

    def properties(self):
        return self.node.properties()

    def compute(self):
        return self.node.compute()

    def visualise(self, height, wh_ratio):
        return self.node.visualise(height, wh_ratio)


class ShapeNode(CombinationNode):
    SELECTIONS = [PolygonNode, EllipseNode]

    def __init__(self, node_id, input_nodes, properties):
        super().__init__(node_id, input_nodes, properties)
        self.node = ShapeNode.SELECTIONS[properties['_selection']](node_id, input_nodes, properties)


node_classes = [CanvasNode, PosWarpNode, RelWarpNode, GridNode, ShapeRepeaterNode, ShapeNode,
                CheckerboardNode,
                CubicFunNode, CustomFunNode, PiecewiseFunNode]
