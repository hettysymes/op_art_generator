import svgwrite
import cairosvg
import math

class Drawing:

    def __init__(self, out_name, width, height):
        self.out_name = out_name
        self.width = width
        self.height = height
        self.dwg = svgwrite.Drawing(f'{out_name}.svg', size=(width, height))

    def crop(self, pixel_border=10):
        self.dwg.viewbox(minx=pixel_border, 
                         miny=pixel_border, 
                         width=self.width - 2*pixel_border, 
                         height=self.height - 2*pixel_border)

    def draw(self):
        self.crop()
        self.dwg.add(self.dwg.rect(insert=(0, 0), size=(self.width, self.height), fill="white"))

        # SVG dimensions
        amplitude = 50  # Amplitude of the sine wave
        frequency = 3    # Number of cycles in the sine wave
        num_points = 100  # Number of points to calculate

        # Generate sine wave points
        points = []
        for i in range(num_points):
            y = i * (self.height / num_points)
            x = (self.width / 2) + amplitude * math.sin(2 * math.pi * frequency * (i / num_points))
            points.append((x, y))

        # Create a path string
        path_d = f"M {points[0][0]},{points[0][1]}"  # Move to the first point
        for x, y in points[1:]:
            path_d += f" L {x},{y}"  # Line to subsequent points

        # Add the path to the drawing
        self.dwg.add(self.dwg.path(d=path_d, stroke="blue", fill="none", stroke_width=2))

    def save(self):
        self.dwg.save()
        cairosvg.svg2png(url=f"{self.out_name}.svg", write_to=f"{self.out_name}.png")

if __name__ == '__main__':
    drawing = Drawing('out/example', 800, 400)
    drawing.draw()
    drawing.save()
    print("SVG file saved.")