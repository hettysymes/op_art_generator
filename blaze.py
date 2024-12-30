import svgwrite
import cairosvg
from utils import Circle
import numpy as np

class Drawing:

    def __init__(self, out_name, width, height):
        self.out_name = out_name
        self.width = width
        self.height = height
        self.dwg = svgwrite.Drawing(f'{out_name}.svg', size=(width, height))

    def draw_pt(self, centre, col='green', rad=1):
        self.dwg.add(self.dwg.circle(center=centre, r=rad, fill=col))
        
    def draw(self):
        # Add background
        self.dwg.add(self.dwg.rect(insert=(0, 0), size=(self.width, self.height), fill="white"))
        self.draw_circles()

    def draw_circles(self):
        circles = [Circle(194.45273, 207.26987, 9.8289003),
                   Circle(193.96831, 206.92116, 18.422821),
                   Circle(186.39648, 212.4418, 38.126766),
                   Circle(178.69621, 207.38835, 56.179714),
                   Circle(177.33932, 196.70197, 74.45282),
                   Circle(183.46475, 188.90541, 93.60656),
                   Circle(191.36472, 186.87128, 112.28111),
                   Circle(201.67407, 190.61722, 130.26596),
                   Circle(202.22873, 198.23079, 148.25665)]
        
        zigzag_angles = [0, -np.pi/8, 0, -np.pi/8, 0, -np.pi/8, 0, -np.pi/8, 0]
        circle_samples = []
        for i,c in enumerate(circles):
            self.dwg.add(self.dwg.circle(center=(c.cx, c.cy), r=c.r, fill='none', stroke='red'))
            samples = c.reg_sample(start_angle=zigzag_angles[i], num_samples=50)
            circle_samples.append(samples)
        lines = [list(line) for line in zip(*circle_samples)]
        for line in lines:
            self.dwg.add(self.dwg.polyline(points=line, fill='none', stroke='black'))
                    
    def save(self):
        self.dwg.save()
        cairosvg.svg2png(url=f"{self.out_name}.svg", write_to=f"{self.out_name}.png")

if __name__ == '__main__':
    drawing = Drawing('out/blaze', 400, 400)
    drawing.draw()
    drawing.save()
    print("SVG and PNG files saved.")