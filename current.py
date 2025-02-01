from Drawing import Drawing
from utils import cubic_f, SineWave
from Warp import sample_fun
import numpy as np

class Current(Drawing):

    def __init__(self, out_name, width, height, 
                 trough_peak_y_f=cubic_f(2.4095, -3.8478, 2.3094, 0.0475)):
        super().__init__(out_name, width, height)
        self.trough_peak_y_f = trough_peak_y_f
        self.amplitude = 0.1 * self.width
        self.num_splits = 8
        self.trough_peak_xs = [0.867096363, 0.993142027, 0.886815647, 0.998873766, 0.88618463, 1, 0.936481951, 0.990591667]
        
    def draw(self):
        self.add_bg()
        # split sine wave into multiple parts
        trough_start=True
        ys = sample_fun(self.trough_peak_y_f, self.num_splits)
        points = []
        for i in range(1, len(ys)):
            wavelength = 2 * (ys[i] - ys[i-1])
            sine_wave = SineWave(self.amplitude, wavelength)
            trough_y = ys[i-1] if trough_start else ys[i]
            trough_x = self.trough_peak_xs[i-1] if trough_start else self.trough_peak_xs[i]
            points += sine_wave.sample(trough_x, trough_y, self.trough_peak_xs[i-1], self.trough_peak_xs[i])
            

if __name__ == '__main__':
    drawing = Current('out/current', 1000, 0.75)
    drawing.render()