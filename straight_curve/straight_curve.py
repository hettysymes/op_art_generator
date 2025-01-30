import svgwrite
import cairosvg
import numpy as np

class Drawing:

    def __init__(self, out_name, width, height):
        self.out_name = out_name
        self.width = width
        self.height = height
        self.dwg = svgwrite.Drawing(f'{out_name}.svg', size=(width, height))
        
        # Define clipping that clips everything outside of view box
        clip = self.dwg.defs.add(self.dwg.clipPath(id="viewbox-clip"))
        clip.add(self.dwg.rect(insert=(0, 0), size=(self.width, self.height)))

    # Add element to drawing whilst clipping parts outside the view box
    def dwg_add(self, element):
        element['clip-path'] = "url(#viewbox-clip)"
        self.dwg.add(element)
        
    def draw(self):
        # Add background
        self.dwg_add(self.dwg.rect(insert=(0, 0), size=(self.width, self.height), fill="white"))
        # Add rectangle stripes
        x_fun = lambda x: -1.3*(x**3) + 2*(x**2) + 0.3*x
        y_fun_points = [(0.024, 0.033), (0.220, 0.018), (0.415, 0.035), (0.707, 0.009), (1, 0.033)]
        xy_points, yy_points = zip(*y_fun_points)

        prev_x_boundary = 0
        indices = np.linspace(0, 1, 28)[1:]
        height_fun = lambda i: np.interp(i, xy_points, yy_points)
        for i in indices:
            next_x_boundary = x_fun(i)*self.width
            self.draw_column(next_x_boundary-prev_x_boundary, prev_x_boundary, height_fun)
            prev_x_boundary = next_x_boundary
            #print(i)

    # x_pos is left border of line
    def draw_column(self, rect_w, x_pos, height_fun):
        indices = np.linspace(0, 1, 44)[1:]
        y_pos = 0
        for i in indices:
            rect_h = height_fun(i)*self.height
            print(rect_h)
            self.dwg_add(self.dwg.polygon(
                            points=[(x_pos, y_pos), (x_pos, y_pos+rect_h), (x_pos+rect_w, y_pos+rect_h)],
                            fill='black',
                            stroke='none'
                        ))
            y_pos += rect_h
                    
    def save(self):
        self.dwg.save()
        cairosvg.svg2png(url=f"{self.out_name}.svg", write_to=f"{self.out_name}.png")

if __name__ == '__main__':
    drawing = Drawing('out/straight_curve', 374, 424)
    drawing.draw()
    drawing.save()
    print("SVG and PNG files saved.")