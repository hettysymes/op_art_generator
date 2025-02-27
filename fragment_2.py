from Drawing import Drawing
import numpy as np
import random
from utils import cubic_f
from Warp import PosWarp, sample_fun

class Fragment2(Drawing):

    def __init__(self, out_name, width, height,
                 y_fun = cubic_f(1.5534, -2.2909, 1.4854, 0.1142)):
        super().__init__(out_name, width, height)
        self.y_fun = y_fun
        
    def draw(self):
        self.add_bg() 
        # Make first row
        ys = sample_fun(self.y_fun, 11)*self.height
        xw = 0.0180
        start_x = 0.322
        curvature_w = 0.026*self.width
        xs = np.array([start_x + i*xw for i in range(6)]) * self.width
        beziers = []
        for x in xs:
            beziers.append(self.curve_control_pts(ys[0], ys[1], x, curvature_w))
        for i in range(0, len(beziers)-1, 2):
            self.draw_polygon(beziers[i], beziers[i+1])

    def curve_control_pts(self, y1, y2, x1, curvature_w):
        xm = x1 + curvature_w
        xc = 2 * xm - x1
        yc = (y1+y2)/2
        return [(x1, y1), (xc, yc), (x1, y2)]

    def draw_polygon(self, bezier1, bezier2):
        p0, p1, p2 = bezier1
        p5, p4, p3 = bezier2
        path_data = f"M {p0[0]},{p0[1]} Q {p1[0]},{p1[1]} {p2[0]},{p2[1]} L {p3[0]},{p3[1]} Q {p4[0]},{p4[1]} {p5[0]},{p5[1]} Z"
        self.dwg_add(self.dwg.path(d=path_data, fill="black", stroke="none"))


if __name__ == '__main__':
    drawing = Fragment2('out/fragment_2', 1000, 0.97)
    drawing.render()