from utils import Circle
from Drawing import Drawing

class Blaze(Drawing):

    def __init__(self, out_name, wh_ratio, height,
                 padding_w=0.1):
        super().__init__(out_name, wh_ratio, height)
        # padding_w is (normalised) padding at left and right boundaries
        self.diameter = self.width * (1 - 2*padding_w)

    def draw_pt(self, centre, col='green', rad=1):
        self.dwg.add(self.dwg.circle(center=centre, r=rad, fill=col))
        
    def draw(self):
        self.add_bg()
        
        # Normalised circles where outer circle is centered at (0.5, 0.5) and
        # Diameter of outer circle is 1
        circles = [Circle(0.473775207, 0.530484568, 0.033148261),
                   Circle(0.472141486, 0.529308534, 0.062131517),
                   Circle(0.446605262, 0.547927058, 0.128583662),
                   Circle(0.42063587, 0.530884146, 0.189467771),
                   Circle(0.416059718, 0.494844009, 0.251094369),
                   Circle(0.436717915, 0.468549876, 0.315690932),
                   Circle(0.4633608, 0.461689712, 0.378671412),
                   Circle(0.498129393, 0.474323007, 0.439325858),
                   Circle(0.5, 0.5, 0.5)]
        
        for circle in circles:
            circle.cx *= self.width
            circle.cy *= self.height
            circle.scale(self.diameter)
        
        zigzag_angles = [1.563889958, 1.514036403, 1.165083633, 1.516246349, 1.191979318, 1.438082975, 1.132194804, 1.406996157, 1.081285523]
        circle_samples = []
        for i,c in enumerate(circles):
            # self.dwg.add(self.dwg.circle(center=(c.cx, c.cy), r=c.r, fill='none', stroke='red'))
            samples = c.reg_sample(start_angle=zigzag_angles[i], num_samples=144)
            circle_samples.append(samples)
        lines = [list(line) for line in zip(*circle_samples)]
        for i in range(0, len(lines), 2):
            left_line = lines[i-1]
            right_line = lines[i]
            right_line.reverse()
            points = left_line + right_line
            path = self.create_line_path(points, fill='black', colour='black')
            path.push('Z')
            self.dwg.add(path)

    def create_line_path(self, points, colour='blue', fill='none', stroke_width=1):
        path = self.dwg.path(stroke=colour, fill=fill, stroke_width=stroke_width)
        path.push('M', points[0][0], points[0][1])  # Move to start point
        for i in range(1, len(points)):
            path.push('L', points[i][0], points[i][1])
        return path

if __name__ == '__main__':
    drawing = Blaze('out/blaze', 2500, 1)
    drawing.render()