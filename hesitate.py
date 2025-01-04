import svgwrite
import subprocess
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
        # Define merge centre x position
        merge_y = self.height * 3/8
        # Add rectangle stripes
        start = True
        switch = False
        ellipse_rw = 10
        y_pos = 0
        while y_pos < self.height:
            # Use sigmoid fun to find rectangle width
            # 1.5 is arbitrary scaling factor for "sharper" curve
            d = 1.5*abs(merge_y - y_pos)
            sigmoid = lambda z: 1/(1 + math.exp(-z))
            # Consider sigmoid range [a, b]
            a = -2.3
            b = 4
            # When x is high, sigmoid is close to 1 so rect_w is approx rect_h
            ellipse_rh = ellipse_rw * sigmoid(a + (d/merge_y) * (b-a))
            self.add_verticle_stripe(ellipse_rw, ellipse_rh, y_pos, start)
            y_pos += 2*ellipse_rh
            start = not start
        self.add_gradients()

    def add_gradients(self):
        # Define a blur filter
        blur_filter = self.dwg.defs.add(self.dwg.filter(id='blur'))
        blur_filter.feGaussianBlur(in_='SourceGraphic', stdDeviation=10)

        # Draw the Bezier path with blurred stroke
        path = self.dwg.path(d="M100,250 C150,100 350,100 400,250", stroke="white", fill="none", stroke_width=20)
        path['filter'] = 'url(#blur)'

        # Add to canvas
        self.dwg.add(path)

    # x_pos is left border of line
    def add_verticle_stripe(self, ellipse_rx, ellipse_ry, y_pos, start=True):
        x_pos = 0
        if not start:
            # White area starts
            x_pos += 2*ellipse_rx
        while x_pos < self.width:
            self.dwg.add(self.dwg.ellipse(
                            center=(x_pos, y_pos),
                            r=(ellipse_rx, ellipse_ry),
                            fill='black',
                        ))
            x_pos += 4*ellipse_rx

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
    drawing = Drawing('out/hesitate', 400, 400)
    drawing.draw()
    drawing.save()
    print("SVG and PNG files saved.")