from Drawing import Drawing
from Warp import PosWarp
import numpy as np

class MovementInSquares(Drawing):

    def __init__(self, out_name, width, height, 
                 num_gridlines=32,
                 rect_h=0.077,
                 gridline_f=lambda i: (3.2206*(i**3) - 5.4091*(i**2) + 3.1979*i)/1.0094000000000007,
                 black_rect_starts=True):
        super().__init__(out_name, width, height)
        self.num_gridlines = num_gridlines
        self.rect_h = rect_h * self.height
        self.gridline_f = gridline_f
        self.black_rect_starts = black_rect_starts
        
    def draw(self):
        self.add_bg()
        black_rect_starts = self.black_rect_starts
        gridline_warp = PosWarp(self.gridline_f)
        gridline_xs = gridline_warp.sample(self.num_gridlines)*self.width
        for i in range(1, len(gridline_xs)):
            x = gridline_xs[i-1]
            rect_w = gridline_xs[i] - x
            self.draw_column(x, rect_w, black_rect_starts)
            black_rect_starts = not black_rect_starts

    def draw_column(self, x, rect_w, black_rect_starts):
        # A block is two stacked rectangles (one black, one white)
        block_ys = np.arange(0, self.height, 2*self.rect_h)
        for block_y in block_ys:
            y = block_y if black_rect_starts else block_y + self.rect_h
            self.dwg_add(self.dwg.rect(
                            insert=(x, y),
                            size=(rect_w, self.rect_h),
                            fill='black',
                            ))

if __name__ == '__main__':
    drawing = MovementInSquares('out/movement_in_squares', 492, 492)
    drawing.render()