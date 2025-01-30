from Drawing import Drawing
from Warp import PosWarp, RelWarp
import numpy as np

class StraightCurve(Drawing):

    def __init__(self, out_name, width, height, 
                 num_vlines=28,
                 num_hlines=44,
                 vline_f=lambda i: -1.3*(i**3) + 2*(i**2) + 0.3*i,
                 hline_piecewise_f_pts=[(0.024, 0.033), (0.220, 0.018), (0.415, 0.035), (0.707, 0.009), (1, 0.033)]):
        super().__init__(out_name, width, height)
        self.num_vlines = num_vlines
        self.num_hlines = num_hlines
        self.vline_f = vline_f
        xs, ys = zip(*hline_piecewise_f_pts)
        self.hline_f = lambda i: np.interp(i, xs, ys)

    def draw(self):
        self.add_bg()
        vline_xs = PosWarp(self.vline_f).sample(self.num_vlines)*self.width
        hline_ys = RelWarp(self.hline_f).sample(self.num_hlines)*self.height
        for i in range(1, len(vline_xs)):
            self.draw_column(vline_xs[i-1], vline_xs[i], hline_ys)

    def draw_column(self, x1, x2, hline_ys):
        for i in range(1, len(hline_ys)):
            y1 = hline_ys[i-1]
            y2 = hline_ys[i]
            self.dwg_add(self.dwg.polygon(
                            points=[(x1, y1), (x1, y2), (x2, y2)],
                            fill='black',
                            stroke='none'
                        ))

if __name__ == '__main__':
    drawing = StraightCurve('out/straight_curve', 374, 424)
    drawing.render()