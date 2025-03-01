from Warp import PosWarp
from Drawing import Drawing
from utils import cubic_f

class InvalidInputNodesLength(Exception):
    """Custom exception for incorrect input_nodes length."""
    def __init__(self, expected_length, actual_length):
        super().__init__(f"Expected {expected_length} input node(s), but got {actual_length}.")

class GridNode:

    def __init__(self, node_id, input_nodes, properties):
        if len(input_nodes) != 0:
            raise InvalidInputNodesLength(0, len(input_nodes))
        self.node_id = node_id
        self.num_v_lines = properties['num_v_lines']
        self.num_h_lines = properties['num_h_lines']

        if properties['function_type'] == 'cubic':
            self.x_warp_f = cubic_f(properties['cubic_param_a'],
                                    properties['cubic_param_b'],
                                    properties['cubic_param_c'],
                                    properties['cubic_param_d'])
        else:
            xs, ys = zip(*properties['piecewise_points'])
            self.x_warp_f = lambda i: np.interp(i, xs, ys)

        self.y_warp_f = lambda i: i

    def compute(self, height, wh_ratio):
        width = wh_ratio * height
        v_line_xs = PosWarp(self.x_warp_f).sample(self.num_v_lines)*width
        h_line_ys = PosWarp(self.y_warp_f).sample(self.num_h_lines)*height
        return v_line_xs, h_line_ys

    def visualise(self, height, wh_ratio):
        d = GridDrawing(str(self.node_id), height, wh_ratio, self.compute(height, wh_ratio))
        return d.save()

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
        if len(input_nodes) != 1:
            raise InvalidInputNodesLength(1, len(input_nodes))
        self.node_id = node_id
        self.grid_node = input_nodes[0]
        self.shape = properties['shape']

    def compute(self, height, wh_ratio):
        v_line_xs, h_line_ys = self.grid_node.compute(height, wh_ratio)
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
        d = ShapeRepeaterDrawing(str(self.node_id), height, wh_ratio, self.compute(height, wh_ratio))
        return d.save()

class ShapeRepeaterDrawing(Drawing):

    def __init__(self, out_name, height, wh_ratio, inputs):
        super().__init__(out_name, height, wh_ratio)
        self.polygons = inputs

    def draw(self):
        self.add_bg()
        for p in self.polygons:
            self.dwg_add(self.dwg.polygon(**p))