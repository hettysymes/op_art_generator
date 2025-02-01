from Drawing import Drawing
from Warp import sample_fun
import numpy as np
from utils import SineWave
import itertools

class Arrest2(Drawing):

    def __init__(self, out_name, wh_ratio, height,
                 colours=['#29272e', '#3f4957', '#818389'],
                 trough_x_f=lambda i: 0.7458*(i**3) - 0.8916*(i**2) + 1.0888*i + 0.0084,
                 num_waves=30,
                 amplitude=0.0195,
                 wavelength=0.281,
                 phase_shift_f=lambda i: 9.1 - abs(21*i - 9.1),
                 first_sine_trough_y=0.059,
                 gradient_wave_bound=0.6333):
        super().__init__(out_name, wh_ratio, height)
        self.colour_it = itertools.cycle(colours)
        self.trough_x_f = trough_x_f
        self.num_waves = num_waves
        self.amplitude = amplitude*self.width
        self.wavelength = wavelength*self.height
        self.phase_shift_f = phase_shift_f
        self.first_sine_trough_y = first_sine_trough_y * self.height
        self.gradient_wave_bound = np.clip(round(gradient_wave_bound * num_waves)-1, 0, num_waves-1)
        
    def draw(self):
        self.add_bg()

        # Get sine wave properties
        trough_xs = sample_fun(self.trough_x_f, self.num_waves)*self.width
        phase_shifts = sample_fun(self.phase_shift_f, self.num_waves)
        sine = SineWave(self.amplitude, self.wavelength)

        # Get sine wave points
        wave_points = []
        for i in range(self.num_waves):
            distance_shift = (self.wavelength / (2*np.pi)) * phase_shifts[i]
            trough_y = self.first_sine_trough_y + distance_shift
            horizontal_points = sine.sample(trough_y, trough_xs[i], 0, self.height)
            wave_points.append([(x,y) for (y,x) in horizontal_points])

        # Draw the sine wave polygons
        for i in range(1, len(wave_points), 2):
            points = wave_points[i-1] + list(reversed(wave_points[i]))
            self.dwg_add(self.dwg.polygon(points, fill=next(self.colour_it), stroke='none'))

        # Add gradients
        self.add_gradients(wave_points)

    def add_gradients(self, wave_points):
        grad_end_sine_pts = wave_points[self.gradient_wave_bound]
        grad_id = self.create_linear_gradient()
        # Add first gradient
        self.dwg_add(self.dwg.polygon(grad_end_sine_pts + [(0, self.height), (0, 0)], fill=f'url(#{grad_id})'))
        # Add second gradient
        self.dwg_add(self.dwg.polygon(grad_end_sine_pts + [(self.width, self.height), (self.width, 0)], fill=f'url(#{grad_id})'))

    def create_linear_gradient(self, colour='white'):
        grad_id = 'white_lin_grad'
        gradient = self.dwg.linearGradient(id=grad_id, start=(0, 0), end=(1, 0))  # From left to right
        gradient.add_stop_color(offset=0, opacity=0, color=colour)  # Start with transparent
        gradient.add_stop_color(offset=1, opacity=1, color=colour)  # End with white
        self.dwg.defs.add(gradient)
        return grad_id

if __name__ == '__main__':
    drawing = Arrest2('out/arrest_2', 1000, 0.981)
    drawing.render()