from Drawing import Drawing
from Warp import RelWarp
import numpy as np

class Hesitate(Drawing):

    def __init__(self, out_name, width, height,
                 rx=0.02,
                 ry_f=lambda i: min(0.052*abs(i-0.365)+0.001, 0.02),
                 num_hlines=37,
                 ellipse_start=True):
        super().__init__(out_name, width, height)

        # Parameters
        self.rx = rx*self.width
        self.height_f = lambda i: ry_f(i)*2
        self.num_hlines = num_hlines
        self.ellipse_start = ellipse_start
        
    def draw(self):
        self.add_bg('#eceeeb')
        block_xs = np.arange(0, self.width, 4*self.rx)
        hline_ys = RelWarp(self.height_f).sample(self.num_hlines)*self.height
        ellipse_start = self.ellipse_start
        for i in range(1, len(hline_ys)):
            y1 = hline_ys[i-1]
            y2 = hline_ys[i]
            ry = (y2-y1)/2
            for block_x in block_xs:
                x = block_x if ellipse_start else block_x + 2*self.rx
                self.dwg_add(self.dwg.ellipse(
                                center=(x+self.rx, y1+ry),
                                r=(self.rx, ry),
                                fill='black',
                                ))
            ellipse_start = not ellipse_start

if __name__ == '__main__':
    drawing = Hesitate('out/hesitate', 414, 394)
    drawing.render()