from Drawing import Drawing
import random
from utils import cubic_f
from Warp import sample_fun
import numpy as np

class CurveRow:

        def __init__(self, fragment2, x1, y1, y2, num_curves, left, curvature_w):
            self.x1 = x1
            self.y1 = y1
            self.y2 = y2
            self.num_curves = num_curves
            self.left = left
            self.curvature_w = curvature_w
            self.fragment2 = fragment2

        def draw(self):
            xs = [self.x1 + i*self.fragment2.polygon_w for i in range(self.num_curves+1)]
            beziers = []
            for x in xs:
                beziers.append(self.curve_control_pts(self.y1, self.y2, x, self.left, self.curvature_w))
            for i in range(0, len(xs)-1):
                fill = 'black' if i%2 == 0 else '#d1d2d4'
                self.draw_polygon(beziers[i], beziers[i+1], fill)

        def curve_control_pts(self, y1, y2, x1, left, curvature_w):
            xm = x1 - curvature_w if left else x1 + curvature_w
            xc = 2 * xm - x1
            yc = (y1+y2)/2
            return [(x1, y1), (xc, yc), (x1, y2)]

        def draw_polygon(self, bezier1, bezier2, fill):
            p0, p1, p2 = bezier1
            p5, p4, p3 = bezier2
            path_data = f"M {p0[0]},{p0[1]} Q {p1[0]},{p1[1]} {p2[0]},{p2[1]} L {p3[0]},{p3[1]} Q {p4[0]},{p4[1]} {p5[0]},{p5[1]} Z"
            self.fragment2.dwg_add(self.fragment2.dwg.path(d=path_data, fill=fill, stroke="none"))

class Fragment2(Drawing):

    def __init__(self, out_name, width, height,
                 y_fun = cubic_f(1.5534, -2.2909, 1.4854, 0.1142),
                 polygon_w = 0.018):
        super().__init__(out_name, width, height)
        self.y_fun = y_fun
        self.polygon_w = polygon_w * self.width
        self.num_rows = 11
        
    def draw(self):
        self.add_bg() 
        ys = sample_fun(self.y_fun, self.num_rows)*self.height
        mean_ncs = np.linspace(4, 40, self.num_rows)
        row = CurveRow(self, 0.322*self.width, ys[0], ys[1], 5, False, 0.026*self.width)
        row.draw()
        for i in range(2, len(ys)):
            row = self.gen_row(row, ys[i], mean_ncs[i])
            row.draw()

    def gen_row(self, prev_row, y2, nc_mean):
        num_curves = int(np.random.normal(loc=nc_mean, scale=1.0))
        shift = random.randint(-2, 2)
        flip = random.random() < 0.5
        left = (not prev_row.left) if flip else prev_row.left
        curvature_w = random.uniform(0.02, 0.08)*self.width
        return CurveRow(self, prev_row.x1 + shift*self.polygon_w, prev_row.y2, y2, num_curves, left, curvature_w)


if __name__ == '__main__':
    drawing = Fragment2('out/fragment_2', 1000, 0.97)
    drawing.render()