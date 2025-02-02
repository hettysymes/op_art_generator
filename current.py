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
        self.x_diffs = np.array([0.126045664, -0.10632638, 0.112058119, -0.112689136, 0.113977462, -0.063680142, 0.054109716]) * self.width
        num_waves = 80
        self.x_starts = np.linspace(-100, self.width, num_waves)

        # Interpolate top and bottom curve
        half_wavelength1 = self.ys[1] - self.ys[0]
        peak1_y = self.ys[0] - half_wavelength1
        half_wavelength2 = self.ys[-1] - self.ys[-2]
        peak2_y = self.ys[-1] + half_wavelength2
        self.ys = np.insert(self.ys, 0, peak1_y)
        self.ys = np.append(self.ys, peak2_y)
        
    def draw(self):
        self.add_bg()

        for x_start in self.x_starts:
            xs = [x_start]
            for d in self.x_diffs:
                xs.append(xs[-1] + d)
            
            # Interpolate top and bottom curve
            twice_amplitude1 = abs(xs[1] - xs[0])
            peak1_x = xs[0] + twice_amplitude1
            twice_amplitude2 = abs(xs[-1] - xs[-2])
            peak2_x = xs[-1] - twice_amplitude2
            xs.insert(0, peak1_x)
            xs.append(peak2_x)

            curve = CatmullRomCurve(list(zip(xs, self.ys)))
            points = curve.regular_sample()
            self.dwg_add(self.dwg.polyline(points, fill='none', stroke='black'))
            

if __name__ == '__main__':
    drawing = Current('out/current', 1000, 0.75)
    drawing.render()