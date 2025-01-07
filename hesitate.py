import svgwrite
import subprocess
import math

class Drawing:

    def __init__(self, out_name, width, height):
        self.out_name = out_name
        self.width = width
        self.height = height
        self.dwg = svgwrite.Drawing(f'{out_name}.svg', size=(width, height))

        # Parameters
        self.merge_y = 58.4
        self.rx = 4.03

        scale = 0.28
        min_ry = 0.25
        self.ry_fun = lambda idx: abs(scale*idx)+min_ry

        
    def draw(self):
        # Add background
        self.dwg.add(self.dwg.rect(insert=(0, 0), size=(self.width, self.height), fill="white"))

        init_ry, init_y_pos, _ = self.draw_row(0, 0, self.merge_y, True)
        # Draw from merge to top
        ry = init_ry
        y_pos = init_y_pos
        idx = -1
        while y_pos > 0:
            ry, y_pos, idx = self.draw_row(idx, ry, y_pos, True)

        # Draw from merge to bottom
        ry = init_ry
        y_pos = init_y_pos
        idx = 1
        while y_pos < self.height:
            ry, y_pos, idx = self.draw_row(idx, ry, y_pos, False)
        
        #self.add_gradients()

    def add_gradients(self):
        # Define a blur filter
        blur_filter = self.dwg.defs.add(self.dwg.filter(id='blur'))
        blur_filter.feGaussianBlur(in_='SourceGraphic', stdDeviation=10)

        # Draw the Bezier path with blurred stroke
        path = self.dwg.path(d="M100,250 C150,100 350,100 400,250", stroke="white", fill="none", stroke_width=20)
        path['filter'] = 'url(#blur)'

        # Add to canvas
        self.dwg.add(path)

    def draw_row(self, idx, prev_ry, prev_y_pos, above):
        ry = self.ry_fun(idx)
        direction = -1 if above else 1
        y_diff = prev_ry + ry
        y_pos = prev_y_pos + direction*y_diff
        x_pos = self.rx if idx % 2 == 0 else self.rx*3
        while x_pos < self.width:
            # Draw ellipse
            self.dwg.add(self.dwg.ellipse(
                            center=(x_pos, y_pos),
                            r=(self.rx, min(self.rx, ry)),
                            fill='black',
                        ))
            x_pos+= self.rx*4
        return ry, y_pos, idx + direction

    def save(self):
        self.dwg.save()
        input_svg = f"{self.out_name}.svg"
        output_png = f"{self.out_name}.png"
        try:
            # Run the Inkscape command
            subprocess.run([
                "/Applications/Inkscape.app/Contents/MacOS/inkscape",
                input_svg,
                "--export-filename", output_png
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    drawing = Drawing('out/hesitate', 207, 197)
    drawing.draw()
    drawing.save()
    print("SVG and PNG files saved.")