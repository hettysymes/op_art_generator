import svgwrite
import subprocess
import numpy as np

class Drawing:

    def __init__(self, out_name, width, height):
        self.out_name = out_name
        self.width = width
        self.height = height
        self.dwg = svgwrite.Drawing(f'{out_name}.svg', size=(width, height))

    def draw(self):
        # Add background
        self.dwg.add(self.dwg.rect(insert=(0, 0), size=(self.width, self.height), fill="white"))

        # Add ellipses
        start = True
        rx = 4.03
        boundary_fun = lambda x: 0.006*(x**3) - 0.2593*(x**2) + 6.5855*x - 0.1371
        prev_boundary = 0
        i = 2
        while prev_boundary < self.height:
            next_boundary = boundary_fun(i)
            ry = (next_boundary - prev_boundary)/2
            self.add_row(prev_boundary+ry, rx, ry, start)
            start = not start
            i += 1
            prev_boundary = next_boundary
        
        #self.add_gradients()

    def add_row(self, y_pos, rx, ry, start=True):
        x_pos = rx
        if not start:
            # Blank area starts
            x_pos += rx*2
        while x_pos < self.width:
            # Draw ellipse
            self.dwg.add(self.dwg.ellipse(
                            center=(x_pos, y_pos),
                            r=(rx, ry),
                            fill='black',
                        ))
            x_pos += rx*4

    def add_gradients(self):
        # Define a blur filter
        blur_filter = self.dwg.defs.add(self.dwg.filter(id='blur'))
        blur_filter.feGaussianBlur(in_='SourceGraphic', stdDeviation=10)

        # Draw the Bezier path with blurred stroke
        path = self.dwg.path(d="M100,250 C150,100 350,100 400,250", stroke="white", fill="none", stroke_width=20)
        path['filter'] = 'url(#blur)'

        # Add to canvas
        self.dwg.add(path)

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