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
        self.top_x_diffs = np.array([0.127333991, -0.109008203, 0.114739941, -0.114450725, 0.114739941, -0.114450725, 0.105090638]) * self.width
        self.bot_x_diffs = np.array([0.127228821, -0.107798753, 0.112031826, -0.112031826, 0.114135217, -0.113214983, 0.103250172]) * self.width
        self.init_top_bot_diff = 0.007940298 * self.width
        num_waves = 80
        self.x_starts = np.linspace(-100, self.width, num_waves)

        # Interpolate top and bottom curve
        half_wavelength1 = self.ys[1] - self.ys[0]
        peak1_y = self.ys[0] - half_wavelength1
        half_wavelength2 = self.ys[-1] - self.ys[-2]
        peak2_y = self.ys[-1] + half_wavelength2
        self.ys = np.insert(self.ys, 0, peak1_y)
        self.ys = np.append(self.ys, peak2_y)

    @staticmethod
    def interpolate_wave_xs(xs):
        twice_amplitude1 = abs(xs[1] - xs[0])
        peak1_x = xs[0] + twice_amplitude1
        twice_amplitude2 = abs(xs[-1] - xs[-2])
        peak2_x = xs[-1] - twice_amplitude2
        xs.insert(0, peak1_x)
        xs.append(peak2_x)
        return xs
        
    def draw(self):
        self.add_bg()

        for x_start in self.x_starts:
            top_xs = [x_start + self.init_top_bot_diff]
            bot_xs = [x_start]
            for d in self.top_x_diffs:
                top_xs.append(top_xs[-1] + d)
            for d in self.bot_x_diffs:
                bot_xs.append(bot_xs[-1] + d)
            
            # Interpolate ends of top and bottom curves
            top_xs = Current.interpolate_wave_xs(top_xs)
            bot_xs = Current.interpolate_wave_xs(bot_xs)

            top_curve = CatmullRomCurve(list(zip(top_xs, self.ys)))
            bot_curve = CatmullRomCurve(list(zip(bot_xs, self.ys)))
            points = top_curve.regular_sample() + list(reversed(bot_curve.regular_sample()))
            self.dwg_add(self.dwg.polygon(points, fill='black', stroke='none'))
            

if __name__ == '__main__':
    drawing = Current('out/current', 1000, 0.75)
    drawing.render()