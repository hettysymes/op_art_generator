import svgwrite
import cairosvg
from utils import CubicBezierCurve
from analyse import get_cubic_beziers

class Drawing:

    def __init__(self, out_name, width, height):
        self.out_name = out_name
        self.width = width
        self.height = height
        self.dwg = svgwrite.Drawing(f'{out_name}.svg', size=(width, height))
        self.set_viewbox()
        self.opacity = 0.1

    # View box is such that (0,0) is the centre of the image
    def set_viewbox(self):
        self.dwg.viewbox(minx=-self.width//2, 
                         miny=-self.height//2, 
                         width=self.width, 
                         height=self.height)
        
    def draw_pt(self, centre, col='green', rad=2):
        self.dwg.add(self.dwg.circle(center=centre, r=rad, fill=col))

    def draw_grid(self, step_size=10, opacity=0.2):
        # Draw horizontal grid lines
        for y in range(-self.width//2, self.width//2, step_size):
            self.dwg.add(self.dwg.line(start=(-self.height//2, y), end=(self.height//2, y), stroke='blue', stroke_width=1, opacity=opacity))

        # Draw vertical grid lines
        for x in range(-self.height//2, self.height//2, step_size):
            self.dwg.add(self.dwg.line(start=(x, -self.width//2), end=(x, self.width//2), stroke='blue', stroke_width=1, opacity=opacity))
        
    def draw(self):
        # Add background
        self.dwg.add(self.dwg.rect(insert=(-self.width//2, -self.height//2), size=(self.width, self.height), fill="white"))
        self.draw_grid()

        p0_pts = CubicBezierCurve([(-61.145489, 19.144546), (-12.962688999999997, -50.87909700000001), (111.10529, -23.679314000000005), (128.24452, 10.170949999999998)])
        p2_pts = CubicBezierCurve([(139.7227, 1.0480200000000002), (70.677453, -140.13314), (-99.901838, -119.80074), (-97.659293, -23.174638), (-97.659293, -23.174638), (-97.053731, 20.426138), (-61.93088, 18.003873), (-61.93088, 18.003873)])
        p3_pts = CubicBezierCurve([(172.42328,-20.752366), (160.75742,-117.4515), (-81.391416,-260.88804), (-176.95926,-7.9394163), (-176.95926,-7.9394163), (-171.59013,26.754865), (-75.920842,23.904545), (-63.142013,18.609439)])

        beziers = [p0_pts, p2_pts, p3_pts]
        cols = ['black', 'blue', 'red']
        for col, b in zip(cols, beziers):
            self.draw_bezier(b, col=col)

    def draw_bezier(self, curve, col='black'):
        self.dwg.add(self.dwg.path(d=curve.path_data(), stroke=col, fill='none'))
        samples = curve.reg_dist_sample(num_samples=20)
        for s in samples:
            self.draw_pt(s)
                    
    def save(self):
        self.dwg.save()
        cairosvg.svg2png(url=f"{self.out_name}.svg", write_to=f"{self.out_name}.png")

if __name__ == '__main__':
    drawing = Drawing('out/circular_movement', 400, 400)
    drawing.draw()
    drawing.save()
    print("SVG and PNG files saved.")