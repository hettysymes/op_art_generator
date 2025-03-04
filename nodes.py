from Warp import PosWarp, RelWarp
from Drawing import Drawing
from utils import cubic_f
import numpy as np
from shapes import Element, Polygon, Ellipse

class EmptyNode:

    def __init__(self, node_id, input_nodes, properties):
        pass

    def compute(self):
        return

    def visualise(self, height, wh_ratio):
        return

class CubicFunNode:

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

class PiecewiseFunNode:

    def __init__(self, node_id, input_nodes, properties):
        self.node_id = node_id
        self.points = properties['points']

    def compute(self):
        xs, ys = zip(*self.points)
        return lambda i: np.interp(i, xs, ys)

    def visualise(self, height, wh_ratio):
        return

class CanvasNode:

    def __init__(self, node_id, input_nodes, properties):
        self.node_id = node_id
        self.input_node = input_nodes[0]

    def get_svg_path(self, height, wh_ratio):
        vis = self.input_node.visualise(height, wh_ratio)
        if vis: return vis
        # No input, return blank canvas
        return BlankCanvas(str(self.node_id), height, wh_ratio).save()

    def compute(self):
        return self.input_node.compute()

    def visualise(self, height, wh_ratio):
        return

class BlankCanvas(Drawing):

    def __init__(self, out_name, height, wh_ratio):
        super().__init__(out_name, height, wh_ratio)

    def draw(self):
        self.add_bg()

class PosWarpNode:

    def __init__(self, node_id, input_nodes, properties):
        self.node_id = node_id
        self.f_node = input_nodes[0]

    def compute(self):
        f = self.f_node.compute()
        if f: return PosWarp(f)

    def visualise(self, height, wh_ratio):
        return

class RelWarpNode:

    def __init__(self, node_id, input_nodes, properties):
        self.node_id = node_id
        self.f_node = input_nodes[0]

    def compute(self):
        f = self.f_node.compute()
        if f: return RelWarp(f)

    def visualise(self, height, wh_ratio):
        return

class GridNode:

    def __init__(self, node_id, input_nodes, properties):
        self.node_id = node_id
        self.num_v_lines = properties['num_v_lines']
        self.num_h_lines = properties['num_h_lines']
        self.x_warp_node, self.y_warp_node = input_nodes

    def compute(self):
        # Get warp functions
        x_warp = self.x_warp_node.compute()
        if x_warp is None:
            x_warp = PosWarp(lambda i: i)

        y_warp = self.y_warp_node.compute()
        if y_warp is None:
            y_warp = PosWarp(lambda i: i)

        v_line_xs = x_warp.sample(self.num_v_lines)
        h_line_ys = y_warp.sample(self.num_h_lines)
        return v_line_xs, h_line_ys

    def visualise(self, height, wh_ratio):
        return GridDrawing(str(self.node_id), height, wh_ratio, self.compute()).save()

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

class ShapeRepeaterNode:

    def __init__(self, node_id, input_nodes, properties):
        self.node_id = node_id
        self.grid_node = input_nodes[0]
        self.element_node = input_nodes[1]

    def compute(self):
        grid_out = self.grid_node.compute()
        element = self.element_node.compute() # TODO: list of polygons
        if grid_out and element:
            v_line_xs, h_line_ys = grid_out
            ret_element = Element()
            for i in range(1, len(v_line_xs)):
                for j in range(1, len(h_line_ys)):
                    x1 = v_line_xs[i-1]
                    x2 = v_line_xs[i]
                    y1 = h_line_ys[j-1]
                    y2 = h_line_ys[j]
                    for shape in element:
                        ret_element.add(shape.scale(x2-x1, y2-y1).translate(x1, y1))
            return ret_element

    def visualise(self, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(str(self.node_id), height, wh_ratio, element).save()

class ElementDrawer(Drawing):

    def __init__(self, out_name, height, wh_ratio, inputs):
        super().__init__(out_name, height, wh_ratio)
        assert isinstance(inputs, Element)
        self.element = inputs

    def draw(self):
        self.add_bg()
        for shape in self.element:
            self.dwg_add(shape.scale(self.width, self.height).get(self.dwg))

class PolygonNode:

    def __init__(self, node_id, input_nodes, properties):
        self.node_id = node_id
        self.points = properties['points']
        self.fill = properties['fill']

    def compute(self):
        return Element([Polygon(self.points, self.fill, 'none')])

    def visualise(self, height, wh_ratio):
        return ElementDrawer(str(self.node_id), height, wh_ratio, self.compute()).save()

class EllipseNode:

    def __init__(self, node_id, input_nodes, properties):
        self.node_id = node_id
        self.rx = properties['rx']
        self.ry = properties['ry']
        self.fill = properties['fill']

    def compute(self):
        return Element([Ellipse((0.5, 0.5), (self.rx, self.ry), self.fill, 'none')])

    def visualise(self, height, wh_ratio):
        return ElementDrawer(str(self.node_id), height, wh_ratio, self.compute()).save()

class CheckerboardNode:

    def __init__(self, node_id, input_nodes, properties):
        self.node_id = node_id
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
                    x1 = v_line_xs[i-1]
                    x2 = v_line_xs[i]
                    y1 = h_line_ys[j-1]
                    y2 = h_line_ys[j]
                    element = element1 if element1_turn else element2
                    for shape in element:
                        ret_element.add(shape.scale(x2-x1, y2-y1).translate(x1, y1))
                    element1_turn = not element1_turn
                element1_starts = not element1_starts
            return ret_element

    def visualise(self, height, wh_ratio):
        element = self.compute()
        if element:
            return ElementDrawer(str(self.node_id), height, wh_ratio, element).save()