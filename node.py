from Warp import PosWarp, RelWarp
from Drawing import Drawing
from utils import cubic_f
import numpy as np

class EmptyNode:

    def __init__(self, node_id, input_nodes, properties):
        pass

    def compute(self, height, wh_ratio):
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

    def compute(self, height, wh_ratio):
        return cubic_f(self.a_coeff, self.b_coeff, self.c_coeff, self.d_coeff)

    def visualise(self, height, wh_ratio):
        return

class PiecewiseFunNode:

    def __init__(self, node_id, input_nodes, properties):
        self.node_id = node_id
        self.points = properties['points']

    def compute(self, height, wh_ratio):
        xs, ys = zip(*self.points)
        return lambda i: np.interp(i, xs, ys)

    def visualise(self, height, wh_ratio):
        return

class CanvasNode:

    def __init__(self, node_id, input_nodes, properties):
        self.node_id = node_id
        self.input_node = input_nodes[0]
        self.wh_ratio = properties['wh_ratio']

    def get_svg_path(self, height):
        vis = self.input_node.visualise(height, self.wh_ratio)
        if vis: return vis
        # No input, return blank canvas
        return BlankCanvas(str(self.node_id), height, self.wh_ratio).save()

    def compute(self, height, wh_ratio):
        return self.input_node.compute(height, wh_ratio)

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

    def compute(self, height, wh_ratio):
        f = self.f_node.compute(height, wh_ratio)
        if f: return PosWarp(f)

    def visualise(self, height, wh_ratio):
        return

class RelWarpNode:

    def __init__(self, node_id, input_nodes, properties):
        self.node_id = node_id
        self.f_node = input_nodes[0]

    def compute(self, height, wh_ratio):
        f = self.f_node.compute(height, wh_ratio)
        if f: return RelWarp(f)

    def visualise(self, height, wh_ratio):
        return

class GridNode:

    def __init__(self, node_id, input_nodes, properties):
        self.node_id = node_id
        self.num_v_lines = properties['num_v_lines']
        self.num_h_lines = properties['num_h_lines']
        self.x_warp_node, self.y_warp_node = input_nodes

    def compute(self, height, wh_ratio):
        # Get warp functions
        x_warp = self.x_warp_node.compute(height, wh_ratio)
        if x_warp is None:
            x_warp = PosWarp(lambda i: i)

        y_warp = self.y_warp_node.compute(height, wh_ratio)
        if y_warp is None:
            y_warp = PosWarp(lambda i: i)

        width = wh_ratio * height
        v_line_xs = x_warp.sample(self.num_v_lines)*width
        h_line_ys = y_warp.sample(self.num_h_lines)*height
        return v_line_xs, h_line_ys

    def visualise(self, height, wh_ratio):
        return GridDrawing(str(self.node_id), height, wh_ratio, self.compute(height, wh_ratio)).save()

class GridDrawing(Drawing):

    def __init__(self, out_name, height, wh_ratio, inputs):
        super().__init__(out_name, height, wh_ratio)
        self.v_line_xs, self.h_line_ys = inputs

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
        self.shape = properties['shape']

    def compute(self, height, wh_ratio):
        output = self.grid_node.compute(height, wh_ratio)
        if output:
            v_line_xs, h_line_ys = output
            polygons = []
            for i in range(1, len(v_line_xs)):
                for j in range(1, len(h_line_ys)):
                    x1 = v_line_xs[i-1]
                    x2 = v_line_xs[i]
                    y1 = h_line_ys[j-1]
                    y2 = h_line_ys[j]
                    polygons.append({'points': [(x1, y1), (x1, y2), (x2, y2)],
                                    'fill': 'black',
                                    'stroke': 'none'})
            return polygons

    def visualise(self, height, wh_ratio):
        polygons = self.compute(height, wh_ratio)
        if polygons:
            return ShapeRepeaterDrawing(str(self.node_id), height, wh_ratio, polygons).save()

class ShapeRepeaterDrawing(Drawing):

    def __init__(self, out_name, height, wh_ratio, inputs):
        super().__init__(out_name, height, wh_ratio)
        self.polygons = inputs

    def draw(self):
        self.add_bg()
        for p in self.polygons:
            self.dwg_add(self.dwg.polygon(**p))