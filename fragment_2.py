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
        for x in xs:
            self.curve_pts(ys[0], ys[1], x, curvature_w)


    def curve_pts(self, y1, y2, x1, curvature_w):
        # Bezier control points
        xm = x1 + curvature_w
        xc = 2 * xm - x1
        yc = (y1+y2)/2
        path_data = f"M {x1},{y1} Q {xc},{yc} {x1},{y2}"
        self.dwg_add(self.dwg.path(d=path_data, stroke="black", fill="none"))

if __name__ == '__main__':
    drawing = Fragment2('out/fragment_2', 1000, 0.97)
    drawing.render()