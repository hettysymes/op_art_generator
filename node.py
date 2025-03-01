from Warp import PosWarp
from Drawing import Drawing
from utils import cubic_f

class GridNode:

    def __init__(self, node_id, num_v_lines, num_h_lines, cubic_param_a):
        self.node_id = node_id
        self.num_v_lines = num_v_lines
        self.num_h_lines = num_h_lines
        self.x_warp_f = cubic_f(cubic_param_a, -5.4091, 3.1979)
        self.y_warp_f = lambda i: i

    def compute(self, height, wh_ratio):
        width = wh_ratio * height
        v_line_xs = PosWarp(self.x_warp_f).sample(self.num_v_lines)*width
        h_line_ys = PosWarp(self.y_warp_f).sample(self.num_h_lines)*height
        return v_line_xs, h_line_ys

    def visualise(self, height, wh_ratio):
        gd = GridDrawing(str(self.node_id), height, wh_ratio, self.compute(height, wh_ratio))
        return gd.save()

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