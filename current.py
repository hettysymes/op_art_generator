from Drawing import Drawing
from utils import cubic_f, CatmullRomCurve
from Warp import sample_fun
import numpy as np

class Current(Drawing):

    def __init__(self, out_name, width, height, 
                 trough_peak_y_f=cubic_f(2.4095, -3.8478, 2.3094, 0.0475)):
        super().__init__(out_name, width, height)
        self.num_splits = 8
        self.ys = sample_fun(trough_peak_y_f, self.num_splits) * self.height
        self.x_diffs = np.array([0.126045664, 0.10632638, 0.112058119, 0.112689136, 0.113977462, 0.063680142, 0.054109716]) * self.width
        num_waves = 80
        self.x_starts = np.linspace(-100, self.width, num_waves)
        
    def draw(self):
        self.add_bg()

        for x_start in self.x_starts:
            xs = [x_start]
            trough = True
            for d in self.x_diffs:
                if trough:
                    xs.append(xs[-1] + d)
                else:
                    xs.append(xs[-1] - d)
                trough = not trough
            curve = CatmullRomCurve(list(zip(xs, self.ys)))
            points = curve.regular_sample()
            self.dwg_add(self.dwg.polyline(points, fill='none', stroke='black'))
            

if __name__ == '__main__':
    drawing = Current('out/current', 1000, 0.75)
    drawing.render()