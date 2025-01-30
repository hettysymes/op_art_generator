from Drawing import Drawing

class MovementInSquares(Drawing):
        
    def draw(self):
        self.add_bg()
        # Add rectangle stripes
        start = True
        rect_h = 9.52
        boundary_fun = lambda x: (3.2206*(x**3) - 5.4091*(x**2) + 3.1979*x)/1.0094
        prev_boundary = 0
        i = 1
        while prev_boundary < self.width:
            next_boundary = boundary_fun(i/31)*self.width
            self.draw_column(next_boundary-prev_boundary, rect_h, prev_boundary, start)
            start = not start
            i += 1
            prev_boundary = next_boundary

    # x_pos is left border of line
    def draw_column(self, rect_w, rect_h, x_pos, start=True):
        y_pos = 0
        if not start:
            # White rectangle starts
            y_pos += rect_h
        while y_pos < self.height:
            self.dwg_add(self.dwg.rect(
                            insert=(x_pos, y_pos),
                            size=(rect_w, rect_h),
                            fill='black',
                        ))
            y_pos += 2*rect_h

if __name__ == '__main__':
    drawing = MovementInSquares('out/movement_in_squares', 123, 123)
    drawing.render()