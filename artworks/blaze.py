from utils import Circle
from Drawing import Drawing

class Blaze(Drawing):

    def __init__(self, out_name, wh_ratio, height,
                 padding_w=0.1,
                 num_zig_zags=72,
                 cxs=[0.473775207, 0.472141486, 0.446605262, 0.42063587, 0.416059718, 0.436717915, 0.4633608, 0.498129393, 0.5],
                 cys=[0.530484568, 0.529308534, 0.547927058, 0.530884146, 0.494844009, 0.468549876, 0.461689712, 0.474323007, 0.5],
                 radii=[0.033148261, 0.062131517, 0.128583662, 0.189467771, 0.251094369, 0.315690932, 0.378671412, 0.439325858, 0.5],
                 zigzag_angles=[1.563889958, 1.514036403, 1.165083633, 1.516246349, 1.191979318, 1.438082975, 1.132194804, 1.406996157, 1.081285523]):
        super().__init__(out_name, wh_ratio, height)
        # padding_w is (normalised) padding at left and right boundaries
        self.diameter = self.width * (1 - 2*padding_w)
        self.num_circle_samples = num_zig_zags * 2
        # Normalised circles where outer circle is centered at (0.5, 0.5) and
        # Diameter of outer circle is 1
        self.circles = [Circle(cxs[i], cys[i], radii[i]) for i in range(len(cxs))]
        self.zigzag_angles = zigzag_angles
        
    def draw(self):
        self.add_bg()
        
        # Scale circle to centre of image with appropriate padding
        for circle in self.circles:
            circle.cx *= self.width
            circle.cy *= self.height
            circle.scale(self.diameter)
        
        # For each circle sample regularly spaced points through which the zig zags go through
        circle_samples = []
        for i, c in enumerate(self.circles):
            samples = c.reg_sample(start_angle=self.zigzag_angles[i], num_samples=self.num_circle_samples)
            circle_samples.append(samples)

        # Connect the circle samples together
        lines = [list(line) for line in zip(*circle_samples)]
        for i in range(0, len(lines), 2):
            points = lines[i-1] + list(reversed(lines[i]))
            self.dwg_add(self.dwg.polygon(points, fill='black', stroke='none'))

if __name__ == '__main__':
    drawing = Blaze('out/blaze', 2500, 1)
    drawing.render()