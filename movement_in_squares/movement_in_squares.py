import svgwrite
import cairosvg
import math

class Drawing:

    def __init__(self, out_name, width, height):
        self.out_name = out_name
        self.width = width
        self.height = height
        self.dwg = svgwrite.Drawing(f'{out_name}.svg', size=(width, height))
        
    def draw(self):
        # Add background
        self.dwg.add(self.dwg.rect(insert=(0, 0), size=(self.width, self.height), fill="white"))
        # Add rectangle stripes
        start = True
        rect_h = 9.52
        boundary_fun = lambda x: 0.0134*(x**3) - 0.7359*(x**2) + 14.176*x - 14.463
        prev_boundary = 0
        i = 2
        while prev_boundary < self.width:
            next_boundary = boundary_fun(i)
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
            self.dwg.add(self.dwg.rect(
                            insert=(x_pos, y_pos),
                            size=(rect_w, rect_h),
                            fill='black',
                        ))
            y_pos += 2*rect_h
                    
    def save(self):
        self.dwg.save()
        cairosvg.svg2png(url=f"{self.out_name}.svg", write_to=f"{self.out_name}.png")

if __name__ == '__main__':
    drawing = Drawing('out/movement_in_squares', 123, 123)
    drawing.draw()
    drawing.save()
    print("SVG and PNG files saved.")