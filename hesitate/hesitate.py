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
        self.rx = 4.03
        scale = 0.28
        min_ry = 0.25
        merge_idx = 14
        self.ry_fun = lambda idx: min(abs(scale*(idx-merge_idx))+min_ry, self.rx)

    def draw(self):
        # Add background
        self.dwg.add(self.dwg.rect(insert=(0, 0), size=(self.width, self.height), fill="white"))

        start = True
        prev_boundary = 0
        i = 1
        while prev_boundary < self.width:
            ry = self.ry_fun(i)
            self.draw_row(prev_boundary + ry, ry, start)
            start = not start
            i += 1
            prev_boundary +=  2*ry
        self.add_gradients()

    def draw_row(self, y_pos, ry, start=True):
        x_pos = self.rx if start else self.rx*3
        while x_pos < self.width:
            # Draw ellipse
            self.dwg.add(self.dwg.ellipse(
                            center=(x_pos, y_pos),
                            r=(self.rx, ry),
                            fill='black',
                        ))
            x_pos += self.rx*4

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