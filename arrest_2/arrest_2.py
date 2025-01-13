import svgwrite
import cairosvg
import numpy as np
from utils import SineWave, ColourIterator

class Drawing:

    def __init__(self, out_name, width, height):
        self.out_name = out_name
        self.width = width
        self.height = height
        self.dwg = svgwrite.Drawing(f'{out_name}.svg', size=(width, height))
        self.colours = {'black': '#29272e', 'blue':'#3f4957', 'grey': '#818389'}
        # Define clipping that clips everything outside of view box
        clip = self.dwg.defs.add(self.dwg.clipPath(id="viewbox-clip"))
        clip.add(self.dwg.rect(insert=(0, 0), size=(self.width, self.height)))

    # Add element to drawing whilst clipping parts outside the view box
    def dwg_add(self, element):
        element['clip-path'] = "url(#viewbox-clip)"
        self.dwg.add(element)
        
    def draw(self):
        # Add background
        self.dwg_add(self.dwg.rect(insert=(0,0), size=(self.width, self.height), fill="white"))
        indices = np.linspace(0, 1, 30)
        trough_xs = [self.width*(0.7458*(x**3) - 0.8916*(x**2) + 1.0888*x + 0.0084) for x in indices]
        phase_shifts = [9.1 - abs(21*x - 9.1) for x in indices]
        amplitude = 0.0195*self.width
        wavelength = 0.281*self.height
        sine = SineWave(amplitude, wavelength)
        first_sine_trough_y = 0.059*self.height

        wave_points = []
        for i in range(len(indices)):
            distance_shift = (wavelength / (2*np.pi)) * phase_shifts[i]
            trough_y = first_sine_trough_y + distance_shift
            horizontal_points = sine.points(trough_y, trough_xs[i], 0, self.height)
            wave_points.append([(x,y) for (y,x) in horizontal_points])

        colour_iterator = ColourIterator([self.colours['black'], self.colours['blue'], self.colours['grey']])
        for i in range(1, len(wave_points), 2):
            points = wave_points[i-1] + list(reversed(wave_points[i]))
            self.dwg_add(self.dwg.polygon(points, fill=colour_iterator.next(), stroke='none'))
            
        
        grad_end_sine_pts = wave_points[18]
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

    def save(self):
        self.dwg.save()
        cairosvg.svg2png(url=f"{self.out_name}.svg", write_to=f"{self.out_name}.png")

if __name__ == '__main__':
    drawing = Drawing('out/arrest_2', 212, 216)
    drawing.draw()
    drawing.save()
    print("SVG and PNG files saved.")