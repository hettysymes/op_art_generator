from Drawing import Drawing
from Warp import PosWarp
import numpy as np

class MovementInSquares(Drawing):

    def __init__(self, out_name, width, height, 
                 num_vert_lines=32,
                 rect_h=0.077,
                 vert_line_f=lambda i: 3.2206*(i**3) - 5.4091*(i**2) + 3.1979*i,
                 black_rect_starts=True):
        super().__init__(out_name, width, height)
        self.num_vert_lines = num_vert_lines
        self.rect_h = rect_h * self.height
        self.vert_line_f= vert_line_f
        self.black_rect_starts = black_rect_starts
        
    def draw(self):
        self.add_bg()
        black_rect_starts = self.black_rect_starts
        vert_line_xs = PosWarp(self.vert_line_f).sample(self.num_vert_lines)*self.width
        for i in range(1, len(vert_line_xs)):
            x = vert_line_xs[i-1]
            rect_w = vert_line_xs[i] - x
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
    drawing = MovementInSquares('out/movement_in_squares', 1000, 1)
    drawing.render()